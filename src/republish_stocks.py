
import argparse
import json
import os
import time

import boto3

kinesis = boto3.client('kinesis')


def encode_record(record: dict) -> bytes:
    return json.dumps(record).encode('utf-8')


def main(args):
    with open('./stocks-data.json') as fp:
      stocks = sorted(json.load(fp), key=lambda x: x['market_time'])

    i, k, n = 0, 0, len(stocks)
    records = []

    while True:
        if i >= n:
            i = 0

        stock = stocks[i]
        records.append({
          'Data': encode_record(stock),
          'PartitionKey': stock['symbol']
        })
        i += 1
        k += 1

        if k > args.batchsize:
            k = 1
            kinesis.put_records(Records=records, StreamName=args.stream)
            print('Published batch: {}'.format(i), json.dumps([r['PartitionKey'] for r in records], indent=4))
            records = []
            time.sleep(args.pause)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stream', help="Name of Kinesis stream to publish to", required=True)
    parser.add_argument('--pause', help='number of seconds to pause between publishing to stream', type=float, default=1)
    parser.add_argument('--batchsize', help="The numnber of records to publish at a time", type=int, default=10)

    args = parser.parse_args()

    main(args)


