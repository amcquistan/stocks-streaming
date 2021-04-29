
import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

DOT_ENVPATH = os.path.join(
  os.path.dirname(os.path.dirname(os.path.abspath('.'))),
  '.env'
)
print(DOT_ENVPATH)
load_dotenv(dotenv_path=DOT_ENVPATH)


STOCK_SUMMARY_ACTION = 'stocks-summary'
STOCK_QUOTES_ACTION = 'stocks-quotes'
STOCK_HISTORY_ACTION = 'stocks-history'


def fetch_stock_quotes(url, headers, params):
    print('url', url)
    print('headers', headers)
    print('params', params)
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    quotes = []
    for quote_data in data['quoteResponse']['result']:
        quotes.append({
          'symbol': quote_data['symbol'],
          'short_name': quote_data['shortName'],
          'market_time': quote_data['regularMarketTime'],
          'quote_source': quote_data['quoteSourceName'],
          'current': quote_data['regularMarketPrice'],
          'low_day': quote_data['regularMarketDayLow'],
          'high_day': quote_data['regularMarketDayHigh'],
          'bid': quote_data['bid'],
          'ask': quote_data['ask'],
          'open': quote_data['regularMarketOpen'],
          'previous_close': quote_data['regularMarketPreviousClose'],
          'low_52wk': quote_data['fiftyTwoWeekLow'],
          'high_52wk': quote_data['fiftyTwoWeekHigh'],
        })

    return quotes


def fetch_stock_history(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    stock_records = []
    timestamps = data['chart']['result'][0]['timestamp']
    symbol = data['chart']['result'][0]['meta']['symbol']
    lows = data['chart']['result'][0]['indicators']['quote'][0]['low']
    highs = data['chart']['result'][0]['indicators']['quote'][0]['high']
    opens = data['chart']['result'][0]['indicators']['quote'][0]['open']
    closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
    for i, ts in enumerate(timestamps):
        stock_records.append({
            'symbol': symbol,
            'market_time': ts,
            'midpoint': (lows[i] + highs[i]) / 2,
            'low': lows[i],
            'high': highs[i],
            'open': opens[i],
            'close': closes[i]
        })
    return stock_records


def fetch_stock_summary(url, headers, params):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', help='The action you want to perform', choices=[STOCK_HISTORY_ACTION, STOCK_QUOTES_ACTION, STOCK_SUMMARY_ACTION])
    parser.add_argument('--symbols', help='Comma separated list of one or more symbols to lookup')
    parser.add_argument('--interval', help='Interval between stock prices for historical stock prices', default='5m', choices=['5m', '15m', '1d', '1wk'])
    parser.add_argument('--range', help='Range between now and given amount to fetch historical stock prices', default='1d', choices=['1d', '5d', '3mo', '6mo'])
    args = parser.parse_args()

    if not args.action:
        print('Need an action')
        sys.exit()

    headers = {
      'x-rapidapi-key': os.environ['YAHOO_X_RAPIDAPI_KEY'],
      'x-rapidapi-host': os.environ['YAHOO_X_RAPIDAPI_HOST']
    }

    query_params = {
      'region': 'US',
    }

    if args.action == STOCK_SUMMARY_ACTION:
        url = os.environ['YAHOO_SUMMARY_URL']
        query_params.update(symbols=','.join([s.strip() for s in args.symbols.split(',')]))
    elif args.action == STOCK_QUOTES_ACTION:
        url = os.environ['YAHOO_QUOTES_URL']
        query_params.update(symbols=','.join([s.strip() for s in args.symbols.split(',')]))
        result = fetch_stock_quotes(url, headers, query_params)
    elif args.action == STOCK_HISTORY_ACTION:
        url = os.environ['YAHOO_CHART_URL']
        query_params.update(
            symbol=args.symbols.strip(),
            interval=args.interval,
            range=args.range
        )
        result = fetch_stock_history(url, headers, query_params)

    print(json.dumps(result, indent=4))
