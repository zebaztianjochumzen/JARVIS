"""Secret resolution — AWS Secrets Manager on EC2, .env fallback for local dev."""

import os
import logging

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")

# Maps each secret to its Secrets Manager path and local env-var fallback
_SECRET_MAP: dict[str, tuple[str, str]] = {
    "ANTHROPIC_API_KEY":  ("jarvis/{env}/anthropic-api-key", "ANTHROPIC_API_KEY"),
    "ELEVENLABS_API_KEY": ("jarvis/{env}/elevenlabs-api-key", "ELEVENLABS_API_KEY"),
}


def get_secret(name: str, environment: str = "dev") -> str:
    """Return a secret value.

    Resolution order:
    1. Environment variable (set in .env for local dev)
    2. AWS Secrets Manager (used on EC2 via instance IAM role)
    """
    secret_path, env_var = _SECRET_MAP[name]

    # 1. Local env var
    value = os.getenv(env_var, "").strip()
    if value:
        return value

    # 2. AWS Secrets Manager
    try:
        import boto3  # noqa: PLC0415 — optional dep, only needed on EC2
        from botocore.exceptions import ClientError

        path = secret_path.format(env=environment)
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        response = client.get_secret_value(SecretId=path)
        return response["SecretString"].strip()
    except ImportError:
        logger.debug("boto3 not installed — Secrets Manager unavailable")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Secrets Manager lookup failed for %s: %s", name, exc)

    raise RuntimeError(
        f"Secret '{name}' not found. "
        f"Set the '{env_var}' environment variable in .env (local) "
        f"or populate 'jarvis/{environment}/{name.lower().replace('_', '-')}' in AWS Secrets Manager."
    )
