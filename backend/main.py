from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import shutil
import sys
import webbrowser
import uvicorn

from database import engine, Base, get_db
import models
from pdf_parser import PDFParser
from expense_logic import auto_categorize, detect_internal_transfers

# Path for bundled assets in PyInstaller
def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(".")

base_path = get_base_path()
frontend_path = os.path.join(base_path, "frontend_dist")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Family Expenses Tracker")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def read_root():
    return {"status": "ok", "message": "Family Expenses Tracker API is running"}

@app.get("/categories/", response_model=List[models.CategoryResponse])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories

@app.get("/transactions/", response_model=List[models.TransactionResponse])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).offset(skip).limit(limit).all()
    return transactions

from pydantic import BaseModel

class TransactionCreate(BaseModel):
    date: str
    amount: float
    description: str
    account_type: str
    bank_name: Optional[str] = None
    category_id: Optional[int] = None

@app.patch("/transactions/{transaction_id}", response_model=models.TransactionResponse)
def update_transaction(transaction_id: int, transaction_update: models.TransactionUpdate, db: Session = Depends(get_db)):
    db_tx = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if transaction_update.category_id is not None:
        db_tx.category_id = transaction_update.category_id
        
    if transaction_update.is_internal_transfer is not None:
        db_tx.is_internal_transfer = transaction_update.is_internal_transfer
        
    db.commit()
    db.refresh(db_tx)
    return db_tx
    account_type: str
    bank_name: Optional[str] = None
    category_id: Optional[int] = None

@app.delete("/transactions/")
def delete_all_transactions(db: Session = Depends(get_db)):
    db.query(models.Transaction).delete()
    db.commit()
    return {"message": "All transactions have been deleted"}

@app.post("/transactions/bulk/")
def bulk_create_transactions(transactions: List[TransactionCreate], db: Session = Depends(get_db)):
    from datetime import datetime
    
    db_txs = []
    for tx in transactions:
        db_tx = models.Transaction(
            date=datetime.strptime(tx.date, "%Y-%m-%d").date(),
            amount=tx.amount,
            description=tx.description,
            account_type=tx.account_type,
            bank_name=tx.bank_name,
            category_id=tx.category_id
        )
        db.add(db_tx)
        db_txs.append(db_tx)
    
    db.commit()
    
    # Recalculate internal transfers
    all_txs = db.query(models.Transaction).all()
    detect_internal_transfers(all_txs)
    db.commit()
    
    return {"message": f"Successfully saved {len(db_txs)} transactions"}

@app.post("/upload/")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save temp file
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        parser = PDFParser(temp_path)
        parsed_result = parser.parse()
        
        raw_data = parsed_result.get("transactions", [])
        bank_name = parsed_result.get("bank_name", "Unknown")
        account_type = parsed_result.get("account_type", "Chequing")
        
        # Mock creating transactions from parsed data
        from datetime import datetime
        import re

        categories = db.query(models.Category).all()
        new_transactions = []
        
        for item in raw_data:
            row = item.get("raw_row", [])
            if len(row) < 3:
                continue
            
            # Reconstruct the line for reliable parsing
            line = " ".join([str(c) for c in row]).strip()
            
            date_val = datetime.today().date()
            amount_val = 0.0
            description_val = "Unknown Transaction"
            
            # 1. Look for amount at the end of the line (e.g. 15.20 or 500.00 CR)
            amt_match = re.search(r'(-?[\d,]+[.,]\d{2})(?:\s+(CR))?$', line, re.IGNORECASE)
            if amt_match:
                amt_str = amt_match.group(1).replace(',', '')
                amount_val = float(amt_str)
                # CR stands for credit, which is a positive flow. Regular amounts are expenses (negative).
                if amt_match.group(2) and amt_match.group(2).upper() == 'CR':
                    amount_val = abs(amount_val)
                else:
                    amount_val = -abs(amount_val)
                # Strip the amount off the description
                line = line[:amt_match.start()].strip()
            
            # 2. Look for date at the start of the line (e.g. Dec. 3 Dec. 5)
            # Use \s* to handle smashed dates like Dec. 10Dec. 10 or 2Jan
            date_match = re.match(r'^([A-Z][a-z]{2}\.?\s+\d{1,2}(?:\s*[A-Z][a-z]{2}\.?\s+\d{1,2})?|\d{1,2}\s*[A-Z][a-z]{2}\.?|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2})\s*', line, re.IGNORECASE)
            
            parsed_month_idx = None
            parsed_day = None
            parsed_iso_date = None
            
            if date_match:
                date_str = date_match.group(1)
                try:
                    if '-' in date_str:
                        parsed_iso_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    else:
                        month_str = None
                        # Check Month Day format (e.g. "Dec. 3")
                        md_match = re.match(r'([A-Za-z]+)\.?\s*(\d+)', date_str)
                        if md_match:
                            month_str = md_match.group(1)[:3].title()
                            parsed_day = int(md_match.group(2))
                        else:
                            # Check Day Month format (e.g. "29 Dec" or "2Jan")
                            dm_match = re.match(r'(\d+)\s*([A-Za-z]+)', date_str)
                            if dm_match:
                                parsed_day = int(dm_match.group(1))
                                month_str = dm_match.group(2)[:3].title()
                                
                        if month_str and parsed_day:
                            parsed_month_idx = datetime.strptime(month_str, '%b').month
                            
                except Exception:
                    pass
                # Strip the date off the description
                line = line[date_match.end():].strip()
                
            if line:
                description_val = line
            
            new_transactions.append({
                "iso_date": parsed_iso_date,
                "month": parsed_month_idx,
                "day": parsed_day,
                "amount": amount_val,
                "description": description_val,
                "account_type": account_type,
                "bank_name": bank_name
            })

        # Dual-Pass Year Resolution
        statement_years = parsed_result.get("statement_years", [datetime.today().year])
        max_year = max(statement_years)
        
        # Check if statement physically bridges a year (contains both Dec and Jan)
        months_present = {tx["month"] for tx in new_transactions if tx["month"] is not None}
        bridging_year = (12 in months_present and 1 in months_present)
        
        db_ready_transactions = []
        for tx in new_transactions:
            if tx["iso_date"]:
                final_date = tx["iso_date"]
            elif tx["month"] and tx["day"]:
                assigned_year = max_year
                # If bridging a year, December (12) and November (11) belong to the previous year
                if bridging_year and tx["month"] >= 11:
                    assigned_year = max_year - 1
                    
                final_date = datetime(assigned_year, tx["month"], tx["day"]).date()
            else:
                final_date = datetime.today().date()
                
            # Create unsaved transaction object for categorization
            new_tx = models.Transaction(
                date=final_date,
                amount=tx["amount"],
                description=tx["description"],
                account_type=tx["account_type"],
                bank_name=tx["bank_name"]
            )
            # Auto-categorize
            new_tx = auto_categorize(new_tx, categories)
            db_ready_transactions.append(new_tx)
            
        return_transactions = []
        for tx in db_ready_transactions:
            return_transactions.append({
                "date": tx.date.isoformat(),
                "amount": tx.amount,
                "description": tx.description,
                "account_type": tx.account_type,
                "bank_name": tx.bank_name,
            })
            
        return {"message": f"Successfully parsed {len(return_transactions)} transactions from {file.filename}", "data": return_transactions}
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Serve Frontend static files
if os.path.exists(frontend_path):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # We need to serve index.html for all non-API paths for React Router
        if full_path.startswith("api/") or full_path.startswith("categories/") or full_path.startswith("transactions/") or full_path.startswith("upload/"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        file_path = os.path.join(frontend_path, full_path)
        # Serve the actual static file if it exists and has an extension (e.g., JS, CSS, images)
        if os.path.isfile(file_path) and "." in os.path.basename(file_path):
            return FileResponse(file_path)
            
        # Otherwise, serve index.html
        index_path = os.path.join(frontend_path, "index.html")
        return FileResponse(index_path)

    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.on_event("startup")
def open_browser():
    # Only open browser once
    if not os.environ.get("BROWSER_OPENED"):
        webbrowser.open("http://127.0.0.1:8000")
        os.environ["BROWSER_OPENED"] = "1"

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
