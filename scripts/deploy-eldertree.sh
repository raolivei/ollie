#!/bin/bash
set -e

# Deploy to ElderTree Pi Cluster

CLUSTER_NAME="eldertree"

echo "Deploying Ollie to $CLUSTER_NAME..."

# Check if context exists
if ! kubectl config get-contexts "$CLUSTER_NAME" > /dev/null 2>&1; then
    echo "Error: Kubernetes context '$CLUSTER_NAME' not found."
    echo "Please ensure your kubeconfig is correctly configured for the Pi cluster."
    echo "If you have a separate kubeconfig file, export KUBECONFIG=/path/to/config"
    exit 1
fi

# Switch context
kubectl config use-context "$CLUSTER_NAME"

# Deploy with Helm
echo "Running Helm upgrade..."
helm upgrade --install ollie helm/ollie \
    --namespace ollie \
    --create-namespace \
    --values helm/ollie/values.yaml

echo "Deployment successful!"
echo "Checking pod status..."
kubectl get pods -n ollie

