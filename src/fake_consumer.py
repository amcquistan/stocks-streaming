
import json
import logging
import random
import time
import sys

from base64 import b64decode
from datetime import datetime

import boto3

STREAM = 'tci-stocks-stream-kinesis-lambda'

logging.basicConfig(
  format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S',
  level=logging.INFO,
  handlers=[
      logging.FileHandler("producer.log"),
      logging.StreamHandler(sys.stdout)
  ]
)


def decode_record(record: bytes) -> dict:
    string_data = record.decode('utf-8')
    return json.loads(string_data)


kinesis = boto3.client('kinesis')

shards_response = kinesis.list_shards(StreamName=STREAM)

import pdb; pdb.set_trace()

shard_iterators = []
for shard in shards_response['Shards']:
    iterator_response = kinesis.get_shard_iterator(
        StreamName=STREAM,
        ShardId=shard['ShardId'],
        ShardIteratorType='AT_SEQUENCE_NUMBER',
        StartingSequenceNumber=shard['SequenceNumberRange']['StartingSequenceNumber']
    )
    shard_iterators.append(iterator_response['ShardIterator'])


while True:
    for i, shard_iterator in enumerate(shard_iterators):
        records_response = kinesis.get_records(ShardIterator=shard_iterator, Limit=10)

        shard_iterators[i] = records_response['NextShardIterator']

        for record in records_response['Records']:
            partition_key = record['PartitionKey']
            data = decode_record(record['Data'])
            logging.info({
              'partition_key': partition_key,
              'data': data
            })

    time.sleep(3)