
import json
import logging
import random
import time
import sys

from base64 import b64encode
from datetime import datetime

import boto3

HIGH_BUMP = 1.02
LOW_BUMP = 0.98
STREAM = 'test-stocks'

logging.basicConfig(
  format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S',
  level=logging.INFO,
  handlers=[
      logging.FileHandler("producer.log"),
      logging.StreamHandler(sys.stdout)
  ]
)

msft_low = 246.88
msft_high = 249.40

amzn_low = 3217.06
amzn_high = 3247.31

kinesis = boto3.client('kinesis')


def encode_record(record: dict) -> bytes:
    return json.dumps(record).encode('utf-8')


records = []

while True:
    if len(records) > 20:
        response = kinesis.put_records(Records=records, StreamName=STREAM)
        logging.info({'kinesis_response': response})
        records = []

    ts = round(datetime.now().timestamp())

    msft_current = random.uniform(msft_low * LOW_BUMP, msft_high * HIGH_BUMP)
    if msft_current < msft_low:
        msft_low = msft_current
    if msft_current > msft_high:
        msft_high = msft_current

    records.append({
      'Data': encode_record({
        'symbol': 'MSFT',
        'market_time': ts,
        'low_day': msft_low,
        'high_day': msft_high,
        'current': msft_current
      }),
      'PartitionKey': 'MSFT'
    })

    amzn_current = random.uniform(amzn_low * LOW_BUMP, amzn_high * HIGH_BUMP)
    if amzn_current < amzn_low:
        amzn_low = amzn_current
    if amzn_current > amzn_high:
        amzn_high = amzn_current

    records.append({
      'Data': encode_record({
        'symbol': 'AMZN',
        'market_time': ts,
        'low_day': amzn_low,
        'high_day': amzn_high,
        'current': amzn_current
      }),
      'PartitionKey': 'MSFT'
    })

    time.sleep(0.25)
