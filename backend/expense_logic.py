from typing import List
from models import Transaction

def auto_categorize(transaction: Transaction, categories: List['Category']):
    """
    Attempts to map a transaction description to a known category.
    """
    desc_lower = transaction.description.lower()
    for cat in categories:
        if cat.keyword:
            keywords = [k.strip().lower() for k in cat.keyword.split(',')]
            for kw in keywords:
                if kw in desc_lower:
                    transaction.category_id = cat.id
                    return transaction
                    
    # Default uncategorized
    transaction.category_id = None
    return transaction


def detect_internal_transfers(transactions: List[Transaction]):
    """
    Identifies internal transfers between accounts.
    A transfer usually consists of a positive and a negative amount of the same absolute value 
    occurring on the exact same date (or within 1 day) across two different accounts.
    """
    # Sort by amount absolute value, then date
    sorted_txs = sorted(transactions, key=lambda x: (abs(x.amount), x.date))
    
    matched_indices = set()
    
    for i in range(len(sorted_txs)):
        if i in matched_indices:
            continue
            
        t1 = sorted_txs[i]
        
        # Look ahead for a matching transaction
        for j in range(i + 1, len(sorted_txs)):
            if j in matched_indices:
                continue
                
            t2 = sorted_txs[j]
            
            # If absolute amounts don't match, we can break early (since sorted)
            if abs(t1.amount) != abs(t2.amount):
                break
                
            # To be a transfer: amounts must be opposite signs, accounts must be different, dates must be close
            opposite_signs = (t1.amount * t2.amount) < 0
            diff_accounts = t1.account_type != t2.account_type
            date_diff = abs((t1.date - t2.date).days)
            
            if opposite_signs and diff_accounts and date_diff <= 1:
                t1.is_internal_transfer = True
                t2.is_internal_transfer = True
                matched_indices.add(i)
                matched_indices.add(j)
                break
                
    return transactions
