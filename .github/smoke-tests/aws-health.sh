#!/usr/bin/env bash
set -euo pipefail

echo "==> [${ENVIRONMENT}] AWS resource health checks"

echo "  Verifying AWS credentials..."
aws sts get-caller-identity --query 'Account' --output text
echo "  ✓ Credentials valid"

# Add resource-specific checks below as you deploy resources.
# Pull values from Terraform outputs like this:
#
#   BUCKET=$(terraform -chdir=terraform output -raw my_bucket_name 2>/dev/null || true)
#   if [[ -n "$BUCKET" ]]; then
#     aws s3api head-bucket --bucket "$BUCKET"
#     echo "  ✓ S3 bucket $BUCKET is accessible"
#   fi
#
#   FUNCTION=$(terraform -chdir=terraform output -raw lambda_function_name 2>/dev/null || true)
#   if [[ -n "$FUNCTION" ]]; then
#     STATE=$(aws lambda get-function --function-name "$FUNCTION" --query 'Configuration.State' --output text)
#     [[ "$STATE" == "Active" ]] || { echo "ERROR: Lambda $FUNCTION is in state $STATE"; exit 1; }
#     echo "  ✓ Lambda $FUNCTION is Active"
#   fi

echo "==> AWS health checks passed"
