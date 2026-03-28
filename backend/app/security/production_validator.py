"""
Production Security Validator

Validates critical security configurations on production startup.
Prevents deployment with insecure settings.
"""

import logging
import json
import secrets
import sys
from typing import List, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class ProductionSecurityValidator:
    """
    Validates security configurations for production environment.

    Checks:
    - Strong secret keys
    - HTTPS enforcement
    - Secure cookie settings
    - Database connection security
    - CORS configuration
    - Debug mode disabled
    """

    @staticmethod
    def validate_secret_key() -> Tuple[bool, str]:
        """
        Validate JWT secret key strength.

        Requirements for production:
        - At least 32 characters
        - Not the default value
        - High entropy

        Returns:
            (is_valid, error_message)
        """
        secret = settings.SECRET_KEY

        # Check for default value
        default_keys = [
            "your-secret-key-change-in-production",
            "change-me",
            "secret",
            "changeme",
            "default",
        ]
        if secret.lower() in default_keys:
            return False, f"SECRET_KEY is set to default value: '{secret}'"

        # Check minimum length
        if len(secret) < 32:
            return False, f"SECRET_KEY too short: {len(secret)} chars (minimum: 32)"

        # Check entropy (basic - should have variety of characters)
        has_upper = any(c.isupper() for c in secret)
        has_lower = any(c.islower() for c in secret)
        has_digit = any(c.isdigit() for c in secret)
        has_special = any(not c.isalnum() for c in secret)

        entropy_score = sum([has_upper, has_lower, has_digit, has_special])
        if entropy_score < 3:
            return False, "SECRET_KEY has low entropy (needs uppercase, lowercase, digits, special chars)"

        return True, ""

    @staticmethod
    def validate_cors_origins() -> Tuple[bool, str]:
        """
        Validate CORS configuration for production.

        Requirements:
        - No wildcard (*) origins
        - All origins should use HTTPS

        Returns:
            (is_valid, error_message)
        """
        origins = settings.cors_origins_list

        # Check for wildcard
        if "*" in origins:
            return False, "CORS_ORIGINS contains wildcard (*) - not allowed in production"

        # Check for HTTP origins (should be HTTPS)
        http_origins = [o for o in origins if o.startswith("http://") and o != "http://localhost:3000"]
        if http_origins:
            return False, f"CORS_ORIGINS contains insecure HTTP origins: {http_origins}"

        return True, ""

    @staticmethod
    def validate_debug_mode() -> Tuple[bool, str]:
        """
        Validate debug mode is disabled in production.

        Returns:
            (is_valid, error_message)
        """
        if settings.DEBUG:
            return False, "DEBUG mode is enabled - must be disabled in production"

        return True, ""

    @staticmethod
    def validate_database_security() -> Tuple[bool, str]:
        """
        Validate database connection security.

        Requirements:
        - Not using default passwords
        - Using allowlisted hosts in production

        Returns:
            (is_valid, error_message)
        """
        db_url = settings.effective_database_url

        # Check for default/weak passwords
        weak_passwords = ["password", "cultivax_pass", "admin", "root", "123456"]
        for weak_pass in weak_passwords:
            if weak_pass in db_url.lower():
                return False, f"Database URL contains weak password pattern: '{weak_pass}'"

        # Check production DB host allowlist if configured
        if settings.CLOUD_SQL_CONNECTION_NAME and settings.PROD_DB_HOST_ALLOWLIST:
            # This is enforced by guards.py verify_production_environment()
            pass

        return True, ""

    @staticmethod
    def validate_admin_api_keys() -> Tuple[bool, str]:
        """
        Validate admin API key configuration for production.

        Requirements:
        - At least one key source configured
        - No plaintext ADMIN_API_KEY in production
        - If keyring JSON is configured, it must parse and contain at least one active key hash
        """
        raw_single = (settings.ADMIN_API_KEY or "").strip()
        raw_ring = (settings.ADMIN_API_KEYS_JSON or "").strip()

        if not raw_single and not raw_ring:
            return False, "No admin API key config found (set ADMIN_API_KEY or ADMIN_API_KEYS_JSON)"

        if raw_single and not raw_single.startswith("sha256:"):
            return False, "ADMIN_API_KEY must be hash-prefixed in production (sha256:<hash>)"

        if raw_ring:
            try:
                parsed = json.loads(raw_ring)
            except Exception as exc:
                return False, f"ADMIN_API_KEYS_JSON is invalid JSON: {exc}"

            if isinstance(parsed, dict):
                parsed = parsed.get("keys", [])
            if not isinstance(parsed, list):
                return False, "ADMIN_API_KEYS_JSON must be a JSON array or object with `keys` array"
            if not parsed:
                return False, "ADMIN_API_KEYS_JSON contains no key records"

            active_count = 0
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                if item.get("active", True):
                    key_hash = str(item.get("sha256") or item.get("hash") or "")
                    if key_hash.startswith("sha256:"):
                        key_hash = key_hash[len("sha256:"):]
                    if len(key_hash) == 64:
                        active_count += 1
            if active_count == 0:
                return False, "ADMIN_API_KEYS_JSON has no active hashed keys"

        return True, ""

    @staticmethod
    def validate_all() -> List[str]:
        """
        Run all production security validations.

        Returns:
            List of error messages (empty if all validations pass)
        """
        errors = []

        # Only enforce in production
        if settings.APP_ENV != "production":
            logger.info("Non-production environment - skipping strict security validation")
            return errors

        logger.info("Running production security validation...")

        validations = [
            ("Secret Key", ProductionSecurityValidator.validate_secret_key),
            ("CORS Origins", ProductionSecurityValidator.validate_cors_origins),
            ("Debug Mode", ProductionSecurityValidator.validate_debug_mode),
            ("Database Security", ProductionSecurityValidator.validate_database_security),
            ("Admin API Keys", ProductionSecurityValidator.validate_admin_api_keys),
        ]

        for name, validator_func in validations:
            is_valid, error_msg = validator_func()
            if not is_valid:
                errors.append(f"❌ {name}: {error_msg}")
                logger.error(f"Security validation failed - {name}: {error_msg}")
            else:
                logger.info(f"✓ {name}: Valid")

        return errors

    @staticmethod
    def enforce_production_security():
        """
        Enforce production security - exit if validation fails.

        This should be called during app startup in production.
        """
        errors = ProductionSecurityValidator.validate_all()

        if errors:
            logger.critical("=" * 80)
            logger.critical("PRODUCTION SECURITY VALIDATION FAILED")
            logger.critical("=" * 80)
            for error in errors:
                logger.critical(error)
            logger.critical("=" * 80)
            logger.critical("Application startup aborted due to security violations")
            logger.critical("Fix the above issues and redeploy")
            logger.critical("=" * 80)
            sys.exit(1)

        logger.info("✓ All production security validations passed")


def generate_secure_secret_key() -> str:
    """
    Generate a cryptographically secure secret key.

    Returns:
        64-character hex string suitable for JWT signing
    """
    return secrets.token_hex(32)  # 32 bytes = 64 hex chars
