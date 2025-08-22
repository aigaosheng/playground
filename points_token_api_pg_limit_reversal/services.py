import datetime
from sqlalchemy.orm import Session
from models import Transaction, PointBatch
from sqlalchemy import func
from config import DAILY_EARN_LIMIT, DAILY_SPEND_LIMIT, DAILY_TRANSFER_LIMIT

def check_daily_limit(db: Session, user_id: str, tx_type: str, amount: int):
    today = datetime.date.today()
    q = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.tx_type == tx_type,
        func.date(Transaction.timestamp) == today
    )
    total = q.scalar() or 0
    limit = 0
    if tx_type == "earn":
        limit = DAILY_EARN_LIMIT
    elif tx_type == "spend":
        limit = DAILY_SPEND_LIMIT
    elif tx_type.startswith("transfer"):
        limit = DAILY_TRANSFER_LIMIT
    if total + amount > limit:
        raise Exception(f"Daily limit exceeded for {tx_type}. limit={limit}, current={total}, request={amount}")

def create_reversal(db: Session, original_tx: Transaction, idempotency_key: str, reason: str):
    # 防止重复冲正
    exists = db.query(Transaction).filter(Transaction.reversal_of == original_tx.id).first()
    if exists:
        raise Exception("This transaction was already reversed.")

    if original_tx.tx_type == "spend":
        # 退回积分
        new_tx = Transaction(
            user_id=original_tx.user_id,
            tx_type="earn",
            amount=original_tx.amount,
            reason=f"reversal:{reason}",
            idempotency_key=idempotency_key,
            reversal_of=original_tx.id
        )
        db.add(new_tx)
    elif original_tx.tx_type == "transfer_out":
        # 给转出方退回
        new_tx1 = Transaction(
            user_id=original_tx.user_id,
            tx_type="earn",
            amount=original_tx.amount,
            reason=f"reversal_out:{reason}",
            idempotency_key=idempotency_key,
            reversal_of=original_tx.id
        )
        # 从接收方扣除
        peer_tx = db.query(Transaction).filter(
            Transaction.reason == original_tx.reason,
            Transaction.tx_type == "transfer_in"
        ).first()
        if not peer_tx:
            raise Exception("Matching transfer_in not found for reversal")
        new_tx2 = Transaction(
            user_id=peer_tx.user_id,
            tx_type="spend",
            amount=peer_tx.amount,
            reason=f"reversal_in:{reason}",
            idempotency_key=idempotency_key + "_peer",
            reversal_of=peer_tx.id
        )
        db.add_all([new_tx1, new_tx2])
    else:
        raise Exception("Unsupported reversal type.")

    db.commit()
    return True
