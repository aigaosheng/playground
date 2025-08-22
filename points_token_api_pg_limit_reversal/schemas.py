from pydantic import BaseModel

class EarnRequest(BaseModel):
    user_id: str
    amount: int
    reason: str
    idempotency_key: str

class SpendRequest(BaseModel):
    user_id: str
    amount: int
    reason: str
    idempotency_key: str

class TransferRequest(BaseModel):
    from_user: str
    to_user: str
    amount: int
    reason: str
    idempotency_key: str

class ReversalRequest(BaseModel):
    original_tx_id: int
    reason: str
    idempotency_key: str
