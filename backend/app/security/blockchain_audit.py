"""
Blockchain-Based Audit Trail

Immutable audit logging using blockchain principles:
- Merkle tree for efficient verification
- Hash chains for tamper detection
- Distributed ledger concepts
- Cryptographic proofs of integrity

Does not require external blockchain - implements internal chain.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class AuditBlock:
    """
    Single block in the audit blockchain.

    Contains multiple audit entries with cryptographic linking.
    """
    index: int
    timestamp: float
    entries: List[Dict[str, Any]]
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def __post_init__(self):
        """Calculate block hash after initialization."""
        if not self.hash:
            self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculate SHA-256 hash of block.

        Includes all block data for tamper detection.
        """
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "entries": self.entries,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }

        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int = 2):
        """
        Mine block with proof-of-work (optional).

        Args:
            difficulty: Number of leading zeros required in hash
        """
        target = "0" * difficulty

        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

        logger.info(f"Block mined: {self.hash} (nonce: {self.nonce})")


class AuditBlockchain:
    """
    Blockchain for immutable audit trails.

    Features:
    - Hash chain linking blocks
    - Merkle tree for efficient verification
    - Tamper detection
    - Cryptographic proof of integrity
    """

    def __init__(self, difficulty: int = 0):
        """
        Initialize blockchain.

        Args:
            difficulty: Mining difficulty (0 = no mining, faster)
        """
        self.chain: List[AuditBlock] = []
        self.pending_entries: List[Dict[str, Any]] = []
        self.difficulty = difficulty

        # Create genesis block
        self.create_genesis_block()

    def create_genesis_block(self):
        """Create the first block in the chain."""
        genesis_block = AuditBlock(
            index=0,
            timestamp=time.time(),
            entries=[{
                "action": "genesis",
                "message": "CultivaX Audit Blockchain Initialized",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
            previous_hash="0",
        )

        if self.difficulty > 0:
            genesis_block.mine_block(self.difficulty)

        self.chain.append(genesis_block)
        logger.info("Genesis block created")

    def get_latest_block(self) -> AuditBlock:
        """Get the most recent block."""
        return self.chain[-1]

    def add_entry(self, entry: Dict[str, Any]):
        """
        Add audit entry to pending entries.

        Args:
            entry: Audit entry data
        """
        # Add timestamp and hash
        entry["_timestamp"] = datetime.now(timezone.utc).isoformat()
        entry["_entry_hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()

        self.pending_entries.append(entry)

        # Auto-commit when we have enough entries
        if len(self.pending_entries) >= 10:
            self.commit_block()

    def commit_block(self) -> Optional[AuditBlock]:
        """
        Commit pending entries to a new block.

        Returns:
            New block, or None if no pending entries
        """
        if not self.pending_entries:
            return None

        latest_block = self.get_latest_block()

        new_block = AuditBlock(
            index=len(self.chain),
            timestamp=time.time(),
            entries=self.pending_entries.copy(),
            previous_hash=latest_block.hash,
        )

        if self.difficulty > 0:
            new_block.mine_block(self.difficulty)

        self.chain.append(new_block)
        self.pending_entries.clear()

        logger.info(f"Block {new_block.index} committed with {len(new_block.entries)} entries")

        return new_block

    def verify_chain(self) -> Tuple[bool, List[str]]:
        """
        Verify integrity of entire blockchain.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Verify block hash
            calculated_hash = current_block.calculate_hash()
            if current_block.hash != calculated_hash:
                errors.append(
                    f"Block {i} has invalid hash: "
                    f"expected {calculated_hash}, got {current_block.hash}"
                )

            # Verify previous hash link
            if current_block.previous_hash != previous_block.hash:
                errors.append(
                    f"Block {i} has broken chain link: "
                    f"previous_hash={current_block.previous_hash}, "
                    f"actual previous={previous_block.hash}"
                )

            # Verify proof-of-work if difficulty > 0
            if self.difficulty > 0:
                required_prefix = "0" * self.difficulty
                if not current_block.hash.startswith(required_prefix):
                    errors.append(
                        f"Block {i} has invalid proof-of-work: "
                        f"hash doesn't start with {required_prefix}"
                    )

        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"Blockchain verified: {len(self.chain)} blocks valid")
        else:
            logger.error(f"Blockchain verification failed: {errors}")

        return is_valid, errors

    def get_merkle_root(self, block_index: int) -> str:
        """
        Calculate Merkle root for a block's entries.

        Provides efficient verification of entry inclusion.

        Args:
            block_index: Block index

        Returns:
            Merkle root hash
        """
        if block_index >= len(self.chain):
            return ""

        block = self.chain[block_index]
        entries = block.entries

        if not entries:
            return hashlib.sha256(b"").hexdigest()

        # Build Merkle tree
        hashes = [
            hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
            for entry in entries
        ]

        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])  # Duplicate last hash if odd

            hashes = [
                hashlib.sha256(
                    (hashes[i] + hashes[i + 1]).encode()
                ).hexdigest()
                for i in range(0, len(hashes), 2)
            ]

        return hashes[0]

    def export_chain(self) -> List[Dict]:
        """
        Export blockchain to JSON format.

        Returns:
            List of block dictionaries
        """
        return [
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "entries": block.entries,
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "nonce": block.nonce,
                "merkle_root": self.get_merkle_root(block.index),
            }
            for block in self.chain
        ]

    def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Query audit trail with filters.

        Args:
            user_id: Filter by user ID
            action_type: Filter by action type
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            Filtered audit entries
        """
        results = []

        for block in self.chain:
            for entry in block.entries:
                # Apply filters
                if user_id and entry.get("user_id") != user_id:
                    continue

                if action_type and entry.get("action") != action_type:
                    continue

                if start_time:
                    entry_time = datetime.fromisoformat(entry.get("_timestamp", ""))
                    if entry_time < start_time:
                        continue

                if end_time:
                    entry_time = datetime.fromisoformat(entry.get("_timestamp", ""))
                    if entry_time > end_time:
                        continue

                # Add block metadata
                results.append({
                    **entry,
                    "_block_index": block.index,
                    "_block_hash": block.hash,
                })

        return results


# Global blockchain instance
_audit_blockchain: Optional[AuditBlockchain] = None


def get_audit_blockchain(difficulty: int = 0) -> AuditBlockchain:
    """
    Get global audit blockchain instance.

    Args:
        difficulty: Mining difficulty (0 for dev, 2+ for production)
    """
    global _audit_blockchain

    if _audit_blockchain is None:
        _audit_blockchain = AuditBlockchain(difficulty=difficulty)

    return _audit_blockchain


def log_to_blockchain(
    action: str,
    user_id: Optional[str] = None,
    details: Optional[Dict] = None,
    **kwargs,
):
    """
    Log action to blockchain audit trail.

    Args:
        action: Action type
        user_id: User performing action
        details: Additional details
        **kwargs: Additional fields
    """
    blockchain = get_audit_blockchain()

    entry = {
        "action": action,
        "user_id": user_id,
        "details": details or {},
        **kwargs,
    }

    blockchain.add_entry(entry)
