-- 'public' schema available by default under 'awsuser'
-- Schema for GTFS data
CREATE SCHEMA IF NOT EXISTS gtfs AUTHORIZATION awsuser;
-- Schema for agency asset data
CREATE SCHEMA IF NOT EXISTS assets AUTHORIZATION awsuser;
-- Schema for EVP data
CREATE SCHEMA IF NOT EXISTS evp AUTHORIZATION awsuser;