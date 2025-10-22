#!/bin/bash
set -e

# Create additional databases for testing if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    
    -- Create test database
    CREATE DATABASE turn_test_db;
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE turn_db TO postgres;
    GRANT ALL PRIVILEGES ON DATABASE turn_test_db TO postgres;
EOSQL

echo "Database initialization completed."