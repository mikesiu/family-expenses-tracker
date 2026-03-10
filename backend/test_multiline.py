import re

cibc_text = """
Jan 9 Balance forward $6,957.26
Jan 12 E-TRANSFER 105780540481 200.00 6,757.26
Marcus
PREAUTHORIZED DEBIT 442.60 6,314.66
IC_9X.J9P_02
Insurance Corporation of BC
Jan 14 PAY 1,048.13 7,362.79
Gap (Canada) In
Gap (Canada) Inc.
"""

transactions = []
prev_balance = None
current_date = None
pending_tx = None # will hold { "desc_words": [], "amount": str }

def flush_tx():
    global pending_tx, transactions, current_date
    if pending_tx and current_date:
        raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
        transactions.append({"raw_row": raw_row_str.split()})
    pending_tx = None

for line in cibc_text.strip().split('\n'):
    line_str = line.strip()
    if not line_str: continue

    # Opening balance
    if "Opening balance" in line_str or "Balance forward" in line_str:
        bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
        if bal_match:
            prev_balance = float(bal_match.group(1).replace(',', ''))
        continue

    # Date check
    date_match = re.match(r'^(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line_str, re.IGNORECASE)
    
    # Amount check
    cibc_cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
    cibc_cred_match = re.search(r'(-?[\d,]+[.,]\d{2})(?:\s*CR)?$', line_str, re.IGNORECASE)

    has_amount = False
    is_cheq = False
    amt_match = None
    
    if cibc_cheq_match:
        has_amount = True
        is_cheq = True
        amt_match = cibc_cheq_match
    elif cibc_cred_match:
        # Ignore things like "105780540481" which are just long numbers. Wait, the regex \d+[.,]\d{2} ensures decimals.
        has_amount = True
        is_cheq = False
        amt_match = cibc_cred_match
        
    if has_amount:
        # It's a new transaction! flush the old one
        flush_tx()
        
        # update date if present
        if date_match:
            current_date = date_match.group(0).strip()
            # strip date from remaining string
            line_str = line_str[date_match.end():].strip()
            
        if is_cheq:
            desc_part = line_str[:line_str.rfind(amt_match.group(0))].strip()
            current_balance = float(amt_match.group(2).replace(',', ''))
            tx_amount = float(amt_match.group(1).replace(',', ''))
            
            amt_str = str(tx_amount)
            if prev_balance is not None:
                if current_balance > prev_balance + 0.01:
                    amt_str += " CR"
            prev_balance = current_balance
            
            pending_tx = {"desc_words": [desc_part] if desc_part else [], "amount": amt_str}
        else:
            desc_part = line_str[:line_str.rfind(amt_match.group(0))].strip()
            pending_tx = {"desc_words": [desc_part] if desc_part else [], "amount": amt_match.group(0)}
            
    else:
        # No amounts. If we have a pending transaction, this is extra description!
        if pending_tx:
            pending_tx["desc_words"].append(line_str)
            
# flush final
flush_tx()

for t in transactions:
    print("row:", " ".join(t["raw_row"]))
