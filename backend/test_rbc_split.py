import re

text_lines = [
    "Details of your account activity",
    "Date Description Withdrawals ($) Deposits ($) Balance ($)",
    "Opening Balance 2,934.80",
    "29 Dec e-Transfer sent Francis Chan Y47UKH 75.40 2,859.40",
    "2 Jan Online Banking transfer - 7367 745.73 2,113.67",
    "5 Jan Investment CANLIFE UNITRX 1,500.00",
    "Investment CANLIFE UNITRX 1,500.00 5,113.67",
    "6 Jan Personal Loan SPL 378.46 4,735.21",
    "Closing Balance $3,370.31"
]

transactions = []
current_date = None
pending_tx = None
prev_balance = None

def flush_tx():
    global pending_tx, current_date, transactions
    if pending_tx and current_date and "amount" in pending_tx:
        raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
        transactions.append({"raw_row": raw_row_str.split()})
        print("Flushed:", raw_row_str)

for line in text_lines:
    line_str = line.strip()
    if not line_str: continue

    # Opening balance
    if "Opening Balance" in line_str and not re.match(r'^\d{1,2}\s+[A-Za-z]{3}\b', line_str):
        bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
        if bal_match:
            prev_balance = float(bal_match.group(1).replace(',', ''))
        continue

    # Filter headers
    if re.search(r'(^Details of your account|^Summary of your account|Your opening balance|Total deposits|Total withdrawals|Your closing balance|^Date\s+Description|Closing Balance)', line_str, re.IGNORECASE):
        flush_tx()
        pending_tx = None
        # Don't reset current_date unless we assume a new context entirely?
        # Actually RBC doesn't repeat dates per row, so it's handled.
        continue

    # Date match: 5 Jan
    date_match = re.match(r'^(\d{1,2}\s+[A-Z][a-z]{2}\.?|\d{1,2}\s+[A-Z]{3})\b', line_str, re.IGNORECASE)
    
    # Dual amount match
    cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
    
    # Single amount match for lines like "5 Jan Investment CANLIFE UNITRX 1,500.00"
    single_amt_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)

    if date_match and cheq_match:
        # standard single-line completed tx
        flush_tx()
        pending_tx = None
        current_date = date_match.group(1).strip()
        
        desc_part = line_str[date_match.end():cheq_match.start()].strip()
        
        tx_amt = float(cheq_match.group(1).replace(',', ''))
        current_balance = float(cheq_match.group(2).replace(',', ''))
        
        amt_str = f"{tx_amt:.2f}"
        if prev_balance is not None and current_balance > prev_balance + 0.01:
            amt_str += " CR"
        prev_balance = current_balance
        
        pending_tx = {"desc_words": [desc_part], "amount": amt_str}
        
    elif date_match and not cheq_match:
        # A new transaction begins on a date line but spans to next line for the amount/balance
        flush_tx()
        current_date = date_match.group(1).strip()
        desc_part = line_str[date_match.end():].strip()
        # strip off the single amount if it's mirrored at the end of line 1
        if single_amt_match:
             desc_part = line_str[date_match.end():single_amt_match.start()].strip()
             
        pending_tx = {"desc_words": [desc_part]}
        
    elif not date_match and cheq_match:
        # A previously started transaction is concluding with amounts
        desc_part = line_str[:cheq_match.start()].strip()
        if pending_tx:
             # RBC often repeats the description on line 2! "Investment CANLIFE UNITRX" vs "Investment CANLIFE UNITRX"
             # So if desc_part is already in the pending descriptions, we can ignore it.
             if desc_part and desc_part not in pending_tx["desc_words"]:
                 pending_tx["desc_words"].append(desc_part)
             
             tx_amt = float(cheq_match.group(1).replace(',', ''))
             current_balance = float(cheq_match.group(2).replace(',', ''))
            
             amt_str = f"{tx_amt:.2f}"
             if prev_balance is not None and current_balance > prev_balance + 0.01:
                 amt_str += " CR"
             prev_balance = current_balance
             
             pending_tx["amount"] = amt_str
             # Since this concludes the transaction, can we flush it? Better to wait for next date or flush at end
        else:
             # Orphaned dual-amount line? Unlikely but possible 
             pass
    else:
        # Just text, add to desc
        if pending_tx:
            # strip single amounts if any from pure desc lines?
            if single_amt_match:
                desc_part = line_str[:single_amt_match.start()].strip()
            else:
                desc_part = line_str
                
            if desc_part and desc_part not in pending_tx["desc_words"]:
                pending_tx["desc_words"].append(desc_part)

flush_tx()
