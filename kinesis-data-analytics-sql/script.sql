
-- ** Multi-step application **
-- Use parallel / serial processing steps.
-- Intermediate, in-application streams are useful for building multi-step applications.
 
--          .------------------.   .-------------------.    .--------------------.              
--          |                  |   |                   |    |                    |              
-- Source-->| STOCK_AGG_STREAM |-->| STOCK_PREV_STREAM |--> | DESTINATION_STREAM |-->Destination
--          |                  |   |                   |    |                    |              
--          '------------------'   '-------------------'    '--------------------'               
-- STREAM (in-application): a continuously updated entity that you can SELECT from and INSERT into like a TABLE
-- PUMP: an entity used to continuously 'SELECT ... FROM' a source STREAM, and INSERT SQL results into an output STREAM
 

CREATE OR REPLACE STREAM "STOCKS_PREV_MIN_MAX_STREAM" (
    "symbol"         VARCHAR(4),
    "low_day"        REAL,
    "prev_low"       REAL,
    "high_day"       REAL,
    "prev_high"      REAL,
    "current_price"  REAL
);

CREATE OR REPLACE PUMP "STOCKS_PREV_MIN_MAX_PUMP" AS
INSERT INTO "STOCKS_PREV_MIN_MAX_STREAM"
SELECT STREAM 
    "SOURCE_SQL_STREAM_001"."symbol" AS "symbol",
    "low_day",
    LAG("low_day", 1, "low_day") OVER WIN_2MIN AS "prev_low",
    "high_day",
    LAG("high_day", 1, "high_day") OVER WIN_2MIN AS "prev_high",
    "COL_current" AS "current_price"
FROM "SOURCE_SQL_STREAM_001"
  WINDOW WIN_2MIN AS (
      PARTITION BY "SOURCE_SQL_STREAM_001"."symbol"
      RANGE INTERVAL '2' MINUTE PRECEDING
    );

CREATE OR REPLACE STREAM "STOCKS_DIFF_STREAM" (
    "symbol"         VARCHAR(4),
    "low_day"        REAL,
    "prev_low"       REAL,
    "high_day"       REAL,
    "prev_high"      REAL,
    "current_price"  REAL
);

CREATE OR REPLACE PUMP "STOCKS_DIFF_PUMP" AS
INSERT INTO "STOCKS_DIFF_STREAM"
SELECT STREAM 
    "symbol",
    "low_day",
    "prev_low",
    "high_day",
    "prev_high",
    "current_price"
FROM "STOCKS_PREV_MIN_MAX_STREAM"
WHERE "low_day" < "prev_low" OR "high_day" > "prev_high";

CREATE OR REPLACE STREAM "STOCKS_AGG_STREAM" (
    "symbol"         VARCHAR(4),
    "low_day"        REAL,
    "prev_low"       REAL,
    "high_day"       REAL,
    "prev_high"      REAL,
    "average_price"  REAL
);

CREATE OR REPLACE PUMP "STOCKS_AGG_PUMP" AS
INSERT INTO "STOCKS_AGG_STREAM"
SELECT STREAM
  "symbol",
  MIN("low_day") AS "low_day",
  MAX("prev_low") AS "prev_low",
  MAX("high_day") AS "high_day",
  MIN("prev_high") AS "prev_high",
  AVG("current_price") AS "average_price"
FROM "STOCKS_DIFF_STREAM"
  GROUP BY 
    "symbol",
    STEP(STOCKS_DIFF_STREAM.ROWTIME BY INTERVAL '2' MINUTE);

CREATE OR REPLACE STREAM "DESTINATION_SQL_STREAM" (
    "symbol"         VARCHAR(4),
    "low_day"        REAL,
    "prev_low"       REAL,
    "high_day"       REAL,
    "prev_high"      REAL,
    "average_price"  REAL
);

CREATE OR REPLACE PUMP "DESTINATION_SQL_PUMP" AS
INSERT INTO "DESTINATION_SQL_STREAM"
SELECT STREAM
  "symbol",
  "low_day",
  "prev_low",
  "high_day",
  "prev_high",
  "average_price"
FROM "STOCKS_AGG_STREAM"
WHERE "low_day" < "prev_low" OR "high_day" > "prev_high";