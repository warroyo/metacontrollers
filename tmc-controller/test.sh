#!/bin/bash

crd_version=${1:-v1}

cleanup() {
  set +e
  echo "Clean up..."
  kubectl delete -f example-ns.yaml
  kubectl delete -k "${crd_version}"
}
trap cleanup EXIT

set -euo

echo "Install controller..."
kubectl apply -k "${crd_version}"

echo "Create a CRD..."
kubectl apply -f example-ns.yaml

echo "Wait for ns create..."
until [[ "$(kubectl get tmcns testing-controller -o 'jsonpath={.status.phase}')" == "Ready" ]]; do sleep 1; done
exit