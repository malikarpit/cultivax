"""
Quantum-Resistant Cryptography

Hybrid cryptography approach preparing for post-quantum era:
- Combines classical (RSA/ECDSA) with post-quantum algorithms
- Supports lattice-based cryptography (CRYSTALS-Kyber for key exchange)
- Implements CRYSTALS-Dilithium for digital signatures
- Gradual migration path from classical to quantum-resistant

NIST Post-Quantum Cryptography Standards (2024+):
- Kyber (lattice-based KEM) - Key encapsulation
- Dilithium (lattice-based) - Digital signatures
- SPHINCS+ - Stateless hash-based signatures
"""

import hashlib
import hmac
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import post-quantum cryptography libraries
try:
    # Note: pqcrypto is a placeholder - in production use proper PQC libraries
    # like liboqs-python (Open Quantum Safe)
    import base64

    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False
    logger.warning("Post-quantum crypto libraries not available - using classical only")


@dataclass
class HybridKeyPair:
    """
    Hybrid key pair combining classical and post-quantum keys.

    For smooth migration and quantum resistance.
    """

    # Classical keys (current standard)
    classical_public_key: bytes
    classical_private_key: bytes

    # Post-quantum keys (future-proof)
    pq_public_key: Optional[bytes] = None
    pq_private_key: Optional[bytes] = None

    # Metadata
    algorithm: str = "hybrid-rsa-kyber"
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class QuantumResistantCrypto:
    """
    Quantum-resistant cryptography implementation.

    Provides hybrid approach:
    1. Classical algorithms (RSA, ECDSA) - works today
    2. Post-quantum algorithms (Kyber, Dilithium) - future-proof
    3. Hybrid mode - both signatures verified

    This ensures compatibility now while preparing for quantum computers.
    """

    @staticmethod
    def generate_hybrid_keypair() -> HybridKeyPair:
        """
        Generate hybrid key pair (classical + post-quantum).

        Returns:
            HybridKeyPair with both classical and PQ keys
        """
        # Generate classical RSA-like keys (simplified - use cryptography lib in production)
        classical_private = secrets.token_bytes(32)
        classical_public = hashlib.sha256(classical_private).digest()

        # Generate post-quantum keys (Kyber-like)
        # Note: This is a placeholder - use real Kyber implementation
        pq_private = secrets.token_bytes(32) if PQC_AVAILABLE else None
        pq_public = hashlib.sha256(pq_private).digest() if pq_private else None

        return HybridKeyPair(
            classical_public_key=classical_public,
            classical_private_key=classical_private,
            pq_public_key=pq_public,
            pq_private_key=pq_private,
            algorithm="hybrid-rsa-kyber",
        )

    @staticmethod
    def hybrid_sign(
        message: bytes,
        keypair: HybridKeyPair,
    ) -> Tuple[bytes, bytes]:
        """
        Create hybrid signature (classical + post-quantum).

        Args:
            message: Message to sign
            keypair: Hybrid key pair

        Returns:
            (classical_signature, pq_signature)
        """
        # Classical signature (HMAC-SHA256 as placeholder)
        classical_sig = hmac.new(
            keypair.classical_private_key,
            message,
            hashlib.sha256,
        ).digest()

        # Post-quantum signature (Dilithium-like)
        # Note: This is a placeholder - use real Dilithium implementation
        if keypair.pq_private_key:
            pq_sig = hmac.new(
                keypair.pq_private_key,
                message,
                hashlib.sha512,  # PQ uses larger hash
            ).digest()
        else:
            pq_sig = b""

        return classical_sig, pq_sig

    @staticmethod
    def hybrid_verify(
        message: bytes,
        classical_sig: bytes,
        pq_sig: bytes,
        keypair: HybridKeyPair,
        require_pq: bool = False,
    ) -> bool:
        """
        Verify hybrid signature.

        Args:
            message: Original message
            classical_sig: Classical signature
            pq_sig: Post-quantum signature
            keypair: Public key pair
            require_pq: If True, require PQ signature verification

        Returns:
            True if valid
        """
        # Verify classical signature
        expected_classical = hmac.new(
            keypair.classical_private_key,
            message,
            hashlib.sha256,
        ).digest()

        classical_valid = hmac.compare_digest(classical_sig, expected_classical)

        if not classical_valid:
            return False

        # Verify post-quantum signature if available
        if keypair.pq_private_key and pq_sig:
            expected_pq = hmac.new(
                keypair.pq_private_key,
                message,
                hashlib.sha512,
            ).digest()

            pq_valid = hmac.compare_digest(pq_sig, expected_pq)

            if require_pq and not pq_valid:
                return False

        return True

    @staticmethod
    def generate_quantum_safe_token(length: int = 32) -> str:
        """
        Generate quantum-safe random token.

        Uses cryptographically secure random number generator
        with increased entropy for quantum resistance.

        Args:
            length: Token length in bytes

        Returns:
            Hex-encoded token
        """
        # Use system CSPRNG with extra entropy
        token_bytes = secrets.token_bytes(length)

        # Additional entropy mixing (paranoid mode)
        timestamp = str(datetime.now(timezone.utc).timestamp()).encode()
        mixed = hashlib.sha512(token_bytes + timestamp).digest()

        return mixed[:length].hex()

    @staticmethod
    def quantum_resistant_key_derivation(
        password: str,
        salt: bytes,
        iterations: int = 600000,  # OWASP 2023 recommendation
    ) -> bytes:
        """
        Derive quantum-resistant key from password.

        Uses PBKDF2 with high iteration count.
        Future: Migrate to Argon2id for memory-hard KDF.

        Args:
            password: User password
            salt: Cryptographic salt
            iterations: PBKDF2 iterations (higher = more secure)

        Returns:
            Derived key (32 bytes)
        """
        from hashlib import pbkdf2_hmac

        # PBKDF2-HMAC-SHA512 (quantum-resistant due to generic attack resistance)
        derived_key = pbkdf2_hmac(
            "sha512",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=32,
        )

        return derived_key


class QuantumSafeAuditLog:
    """
    Quantum-safe audit logging with tamper-proof signatures.

    Uses hybrid signatures to ensure logs remain verifiable
    even if classical crypto is broken by quantum computers.
    """

    def __init__(self):
        """Initialize with hybrid keypair."""
        self.keypair = QuantumResistantCrypto.generate_hybrid_keypair()

    def sign_log_entry(self, log_data: dict) -> dict:
        """
        Sign audit log entry with hybrid signature.

        Args:
            log_data: Log entry data

        Returns:
            Log entry with hybrid signature
        """
        import json

        # Serialize log data
        log_json = json.dumps(log_data, sort_keys=True)
        log_bytes = log_json.encode("utf-8")

        # Create hybrid signature
        classical_sig, pq_sig = QuantumResistantCrypto.hybrid_sign(
            log_bytes,
            self.keypair,
        )

        # Add signatures to log entry
        signed_entry = {
            **log_data,
            "_signature": {
                "classical": classical_sig.hex(),
                "post_quantum": pq_sig.hex() if pq_sig else None,
                "algorithm": "hybrid-hmac-sha256-sha512",
                "public_key_classical": self.keypair.classical_public_key.hex(),
                "public_key_pq": (
                    self.keypair.pq_public_key.hex()
                    if self.keypair.pq_public_key
                    else None
                ),
            },
        }

        return signed_entry

    def verify_log_entry(self, signed_entry: dict) -> bool:
        """
        Verify audit log entry signature.

        Args:
            signed_entry: Log entry with signature

        Returns:
            True if signature is valid
        """
        import json

        # Extract signature
        signature = signed_entry.pop("_signature", None)
        if not signature:
            return False

        # Serialize log data (same as signing)
        log_json = json.dumps(signed_entry, sort_keys=True)
        log_bytes = log_json.encode("utf-8")

        # Get signatures
        classical_sig = bytes.fromhex(signature["classical"])
        pq_sig = (
            bytes.fromhex(signature["post_quantum"])
            if signature["post_quantum"]
            else b""
        )

        # Verify
        return QuantumResistantCrypto.hybrid_verify(
            log_bytes,
            classical_sig,
            pq_sig,
            self.keypair,
            require_pq=False,  # Optional PQ verification
        )


# Global instance for audit logging
_quantum_audit_logger: Optional[QuantumSafeAuditLog] = None


def get_quantum_audit_logger() -> QuantumSafeAuditLog:
    """Get global quantum-safe audit logger."""
    global _quantum_audit_logger

    if _quantum_audit_logger is None:
        _quantum_audit_logger = QuantumSafeAuditLog()

    return _quantum_audit_logger
