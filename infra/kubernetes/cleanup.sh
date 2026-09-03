#!/bin/bash

# Cleanup script - removes all deployed resources
# Use with caution - this deletes all data!

set -e

NAMESPACE="library"

echo "WARNING: This will delete ALL resources in the '$NAMESPACE' namespace!"
echo "This includes all databases and data."
echo ""
read -p "Type 'DELETE' to confirm: " confirmation

if [ "$confirmation" != "DELETE" ]; then
    echo "Aborted."
    exit 0
fi

echo "Deleting namespace and all resources..."
kubectl delete namespace "$NAMESPACE" --ignore-not-found=true

echo "Waiting for resources to be deleted..."
kubectl wait --for=delete namespace/"$NAMESPACE" --timeout=300s 2>/dev/null || true

echo "Cleanup completed."
