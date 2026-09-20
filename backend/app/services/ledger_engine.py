import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ledger import LedgerBlock


class LedgerEngine:
    GENESIS_HASH = "0" * 64

    @staticmethod
    def calculate_hash(index: int, timestamp: str, event_type: str, payload_json: str, previous_hash: str, nonce: int = 0) -> str:
        block_string = f"{index}{timestamp}{event_type}{payload_json}{previous_hash}{nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    @classmethod
    def get_latest_block(cls, db: Session) -> LedgerBlock:
        return db.query(LedgerBlock).order_by(LedgerBlock.index.desc()).first()

    @classmethod
    def append_block(cls, db: Session, event_type: str, payload: dict) -> LedgerBlock:
        latest = cls.get_latest_block(db)
        if not latest:
            # Create Genesis Block
            genesis_time = datetime.utcnow()
            genesis_payload = json.dumps({"message": "Genesis Block - NGO Impact Data Commons Ledger Initialized"})
            genesis_hash = cls.calculate_hash(0, genesis_time.isoformat(), "GENESIS", genesis_payload, cls.GENESIS_HASH, 0)
            genesis_block = LedgerBlock(
                index=0,
                timestamp=genesis_time,
                event_type="GENESIS",
                payload_json=genesis_payload,
                previous_hash=cls.GENESIS_HASH,
                block_hash=genesis_hash,
                nonce=0
            )
            db.add(genesis_block)
            db.commit()
            db.refresh(genesis_block)
            latest = genesis_block

        new_index = latest.index + 1
        new_timestamp = datetime.utcnow()
        payload_json = json.dumps(payload, sort_keys=True, default=str)
        previous_hash = latest.block_hash
        block_hash = cls.calculate_hash(new_index, new_timestamp.isoformat(), event_type, payload_json, previous_hash, 0)

        new_block = LedgerBlock(
            index=new_index,
            timestamp=new_timestamp,
            event_type=event_type,
            payload_json=payload_json,
            previous_hash=previous_hash,
            block_hash=block_hash,
            nonce=0
        )
        db.add(new_block)
        db.commit()
        db.refresh(new_block)
        return new_block

    @classmethod
    def verify_chain(cls, db: Session) -> dict:
        blocks = db.query(LedgerBlock).order_by(LedgerBlock.index.asc()).all()
        if not blocks:
            return {"valid": True, "total_blocks": 0, "status": "Empty ledger"}

        for i, block in enumerate(blocks):
            if i == 0:
                if block.previous_hash != cls.GENESIS_HASH:
                    return {"valid": False, "failed_at_index": 0, "reason": "Invalid Genesis previous hash"}
            else:
                prev_block = blocks[i - 1]
                if block.previous_hash != prev_block.block_hash:
                    return {
                        "valid": False,
                        "failed_at_index": block.index,
                        "reason": f"Previous hash mismatch at index {block.index}"
                    }

            # Recalculate block hash
            expected_hash = cls.calculate_hash(
                block.index,
                block.timestamp.isoformat(),
                block.event_type,
                block.payload_json,
                block.previous_hash,
                block.nonce
            )
            if expected_hash != block.block_hash:
                return {
                    "valid": False,
                    "failed_at_index": block.index,
                    "reason": f"Block hash tampering detected at index {block.index}"
                }

        return {
            "valid": True,
            "total_blocks": len(blocks),
            "latest_hash": blocks[-1].block_hash,
            "status": "Chain verified and tamper-free"
        }
