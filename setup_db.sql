-- Create the psx user if it doesn't exist
CREATE USER psx WITH PASSWORD 'psx' CREATEDB;

-- Create the database if it doesn't exist
CREATE DATABASE psx_fertilizer OWNER psx;

-- Grant all privileges on the database to psx
GRANT ALL PRIVILEGES ON DATABASE psx_fertilizer TO psx;

-- Connect to the database and grant schema privileges
\c psx_fertilizer
GRANT ALL PRIVILEGES ON SCHEMA public TO psx;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO psx;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO psx;

\echo 'Database setup complete!'
