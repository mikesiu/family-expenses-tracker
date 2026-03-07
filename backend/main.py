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
    account_type: str = Form(...),
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
            # Use \s* to handle smashed dates like Dec. 10Dec. 10
            date_match = re.match(r'^([A-Z][a-z]{2}\.?\s+\d{1,2}(?:\s*[A-Z][a-z]{2}\.?\s+\d{1,2})?|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2})\s*', line, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1)
                try:
                    if '-' in date_str:
                        date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                    else:
                        # Fallback for "Dec. 3" or similar formats
                        md_match = re.match(r'([A-Za-z]+)\.?\s+(\d+)', date_str)
                        if md_match:
                            month_str = md_match.group(1)[:3].title()
                            day = int(md_match.group(2))
                            # Using current year as statements often omit the year
                            current_year = datetime.today().year
                            date_val = datetime.strptime(f"{current_year} {month_str} {day}", "%Y %b %d").date()
                except Exception:
                    pass
                # Strip the date off the description
                line = line[date_match.end():].strip()
                
            if line:
                description_val = line
            
            # Create unsaved transaction object for categorization
            tx = models.Transaction(
                date=date_val,
                amount=amount_val,
                description=description_val,
                account_type=account_type,
                bank_name=bank_name
            )
            tx = auto_categorize(tx, categories)
            
            # Append as dictionary to return to frontend for validation
            new_transactions.append({
                "date": tx.date.isoformat(),
                "amount": tx.amount,
                "description": tx.description,
                "account_type": tx.account_type,
                "bank_name": tx.bank_name,
                "category_id": tx.category_id,
                "category_name": tx.category.name if tx.category else (tx.category_id if tx.category_id else "Uncategorized")
            })
            
        return {"message": f"Successfully parsed {len(new_transactions)} transactions from {file.filename}", "data": new_transactions}
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Serve Frontend static files
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_path = os.path.join(frontend_path, "index.html")
        return FileResponse(index_path)

@app.on_event("startup")
def open_browser():
    # Only open browser once
    if not os.environ.get("BROWSER_OPENED"):
        webbrowser.open("http://127.0.0.1:8000")
        os.environ["BROWSER_OPENED"] = "1"

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
