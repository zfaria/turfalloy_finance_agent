#!/usr/bin/env bash

host="$1"
shift
cmd="$@"

until nc -z $host 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL started"
exec $cmd