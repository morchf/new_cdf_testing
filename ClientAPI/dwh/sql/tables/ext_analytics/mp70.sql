CREATE EXTERNAL TABLE ext_analytics.mp70 (
  vehSN TEXT,
  utcTime TIMESTAMP,
  gspd INT,
  gstt INT,
  gpi INT,
  gqal INT,
  ghed INT,
  gsat INT,
  glon FLOAT,
  glat FLOAT
)
PARTITIONED BY (utcdate TEXT) 
STORED AS PARQUET
LOCATION 's3://{MP70_S3_PATH}'
TABLE PROPERTIES ('parquet.compress' = 'SNAPPY')
