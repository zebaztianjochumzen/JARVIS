#!/usr/bin/env bash
set -euo pipefail

echo "==> [${ENVIRONMENT}] AWS resource health checks"

echo "  Verifying AWS credentials..."
aws sts get-caller-identity --query 'Account' --output text
echo "  ✓ Credentials valid"

echo "  Checking EC2 instance state..."
INSTANCE_ID=$(terraform -chdir=terraform output -raw instance_id 2>/dev/null || true)

if [[ -n "$INSTANCE_ID" ]]; then
  STATE=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text)

  if [[ "$STATE" != "running" ]]; then
    echo "ERROR: Instance $INSTANCE_ID is in state '$STATE', expected 'running'"
    exit 1
  fi
  echo "  ✓ Instance $INSTANCE_ID is running"
else
  echo "  No instance ID in outputs — skipping"
fi

echo "==> AWS health checks passed"
