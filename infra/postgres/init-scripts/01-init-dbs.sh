#!/bin/bash
# PostgreSQL initialization script
# Creates separate databases for each microservice

set -e

echo "Creating databases for microservices..."

# Create user_db
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE user_db;
  GRANT ALL PRIVILEGES ON DATABASE user_db TO "$POSTGRES_USER";
EOSQL

# Create book_db
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE book_db;
  GRANT ALL PRIVILEGES ON DATABASE book_db TO "$POSTGRES_USER";
EOSQL

# Create loan_db
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE loan_db;
  GRANT ALL PRIVILEGES ON DATABASE loan_db TO "$POSTGRES_USER";
EOSQL

echo "Databases created successfully!"
