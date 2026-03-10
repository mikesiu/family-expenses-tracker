from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# --- SQLAlchemy Models ---

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    keyword = Column(String) # Comma separated keywords for auto-matching


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    amount = Column(Float)
    description = Column(String)
    merchandiser = Column(String, index=True)
    account_type = Column(String) # e.g., 'Chequing', 'Savings', 'Credit Card'
    bank_name = Column(String, nullable=True) # e.g., 'BMO Mastercard', 'CIBC Visa'
    is_internal_transfer = Column(Boolean, default=False)
    
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")


# --- Pydantic Schemas ---

class CategoryBase(BaseModel):
    name: str
    keyword: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    date: date
    amount: float
    description: str
    merchandiser: Optional[str] = None
    account_type: str
    bank_name: Optional[str] = None
    is_internal_transfer: bool = False
    category_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    is_internal_transfer: Optional[bool] = None

class TransactionResponse(TransactionBase):
    id: int
    category: Optional[CategoryResponse] = None

    class Config:
        orm_mode = True
