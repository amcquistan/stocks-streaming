import datetime
import json
import logging
import os
import time

import boto3
import requests


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
kinesis = boto3.client('kinesis')

UTC_OPEN = datetime.time(14, 30, tzinfo=datetime.timezone.utc)
UTC_CLOSE = datetime.time(21, 00, tzinfo=datetime.timezone.utc)


def encode_record(record: dict) -> bytes:
    bytes_data = json.dumps(record).encode('utf-8')
    return bytes_data


def lambda_handler(event, context):
    now = datetime.datetime.utcnow()
    utc_now = datetime.time(now.hour, now.minute, tzinfo=datetime.timezone.utc)
    if utc_now < UTC_OPEN or utc_now > UTC_CLOSE:
        logger.info({'message': 'Exiting early, {} not during market hours {} - {}'.format(utc_now, UTC_OPEN, UTC_CLOSE)})
        return

    try:
        obj = s3.get_object(Bucket=os.environ['S3_BUCKET'], Key=os.environ['STOCKS_S3KEY'])
        stocks = json.loads(obj['Body'].read().decode('utf-8'))
    except Exception as e:
        logger.error({'error': 'failed_s3_download', 'exception': str(e)})
        raise e

    headers = {
      'x-rapidapi-key': os.environ['YAHOO_X_RAPIDAPI_KEY'],
      'x-rapidapi-host': os.environ['YAHOO_X_RAPIDAPI_HOST']
    }
    query_params = {
        'region': 'US',
        'symbols': ','.join(s for s in stocks['symbols'])
    }
    logger.info({'action': 'fetching_stocks', 'details': query_params})

    for _ in range(3):
        try:
            response = requests.get(os.environ['YAHOO_QUOTES_URL'], headers=headers, params=query_params)
            data = response.json()
        except Exception as e:
            logger.error({'error': 'failed_stocks_fetch', 'exception': str(e)})
            raise e

        records = []
        for quote in data['quoteResponse']['result']:
            records.append({
                'Data': encode_record({
                    'symbol': quote['symbol'],
                    'short_name': quote['shortName'],
                    'market_time': quote['regularMarketTime'],
                    'quote_source': quote['quoteSourceName'],
                    'current': quote['regularMarketPrice'],
                    'low_day': quote['regularMarketDayLow'],
                    'high_day': quote['regularMarketDayHigh'],
                    'open': quote['regularMarketOpen'],
                    'previous_close': quote['regularMarketPreviousClose'],
                    'low_52wk': quote['fiftyTwoWeekLow'],
                    'high_52wk': quote['fiftyTwoWeekHigh'],
                }),
                'PartitionKey': quote['symbol']
            })
        try:
            response = kinesis.put_records(Records=records, StreamName=os.environ['KINESIS_STREAM'])
            logger.info({'action': 'kinesis_put_records', 'response': response})
        except Exception as e:
            logger.error({'error': 'failed_kinesis_fetch', 'exception': str(e)})
            raise e

        time.sleep(10)

    logger.info({'action': 'stock_producer_complete'})
