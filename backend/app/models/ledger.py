from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class LedgerBlock(Base):
    __tablename__ = "ledger_blocks"

    index = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type = Column(String, nullable=False) # e.g. DONATION_LOGGED, NGO_APPROVED, FINANCIAL_RECORD
    payload_json = Column(Text, nullable=False)
    previous_hash = Column(String, nullable=False)
    block_hash = Column(String, unique=True, nullable=False)
    nonce = Column(Integer, default=0)
