#!/usr/bin/env bash
set -euo pipefail

echo "==> [${ENVIRONMENT}] HTTP endpoint checks"

# Add endpoint checks below as you deploy services.
# Pull URLs from Terraform outputs like this:
#
#   ENDPOINT=$(terraform -chdir=terraform output -raw api_endpoint 2>/dev/null || true)
#   if [[ -n "$ENDPOINT" ]]; then
#     STATUS=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 10 "$ENDPOINT/health")
#     [[ "$STATUS" == "200" ]] || { echo "ERROR: $ENDPOINT/health returned HTTP $STATUS"; exit 1; }
#     echo "  ✓ $ENDPOINT/health → HTTP 200"
#   fi

echo "  No HTTP endpoints configured yet — add checks as you deploy services"
echo "==> HTTP checks passed"
