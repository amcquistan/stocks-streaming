#!/bin/bash

aws s3 cp --recursive s3://tci-stocks-stream-kinesis-lambda/stocks-raw stocks-raw

