from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import crud, models, schemas
from services import check_daily_limit, create_reversal

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/earn")
def earn(req: schemas.EarnRequest, db: Session = Depends(get_db)):
    try:
        check_daily_limit(db, req.user_id, "earn", req.amount)
        return crud.earn(db, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/spend")
def spend(req: schemas.SpendRequest, db: Session = Depends(get_db)):
    try:
        check_daily_limit(db, req.user_id, "spend", req.amount)
        return crud.spend(db, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transfer")
def transfer(req: schemas.TransferRequest, db: Session = Depends(get_db)):
    try:
        check_daily_limit(db, req.from_user, "transfer_out", req.amount)
        return crud.transfer(db, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/reversal")
def reversal(req: schemas.ReversalRequest, db: Session = Depends(get_db)):
    original = db.query(models.Transaction).filter(models.Transaction.id == req.original_tx_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Original transaction not found")
    try:
        create_reversal(db, original, req.idempotency_key, req.reason)
        return {"status": "ok", "reversed": req.original_tx_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
