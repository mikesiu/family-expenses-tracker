import re

text_lines = [
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
unbalanced_txs = []

def flush_tx():
    global pending_tx, current_date, transactions
    if pending_tx and current_date and "amount" in pending_tx:
        raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
        transactions.append(raw_row_str)
        print("Flushed:", raw_row_str)
    pending_tx = None

for line in text_lines:
    line_str = line.strip()
    if not line_str: continue

    # Opening balance
    if "Opening Balance" in line_str and not re.match(r'^\d{1,2}\s*[A-Za-z]{3}\b', line_str):
        bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
        if bal_match:
            prev_balance = float(bal_match.group(1).replace(',', ''))
        continue

    # Filter headers
    if re.search(r'(^Details of your account|^Summary of your account|Your opening balance|Total deposits|Total withdrawals|Your closing balance|^Date\s+Description|Closing\s*Balance)', line_str, re.IGNORECASE):
        flush_tx()
        continue

    date_match = re.match(r'^(\d{1,2}\s*[A-Z][a-z]{2}\.?|\d{1,2}\s*[A-Z]{3})\b', line_str, re.IGNORECASE)
    cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
    single_amt_match = re.search(r'\b(-?[\d,]+[.,]\d{2})$', line_str)

    if cheq_match:
        # We hit a line with a balance! Resolves all pending unbalanced txs.
        if date_match:
            current_date = date_match.group(1).strip()
            desc_part = line_str[date_match.end():cheq_match.start()].strip()
        else:
            desc_part = line_str[:cheq_match.start()].strip()
            
        amt = float(cheq_match.group(1).replace(',', ''))
        current_balance = float(cheq_match.group(2).replace(',', ''))
        
        if prev_balance is not None:
            delta = current_balance - prev_balance
            is_credit = delta > 0.01
            
            # Flush any unbalanced txs accumulated earlier
            for utx in unbalanced_txs:
                amt_str = f"{utx['abs_amount']:.2f}"
                if is_credit: amt_str += " CR"
                row = f"{utx['date']} {utx['desc']} {amt_str}"
                transactions.append(row)
                print("Flushed (Resolved):", row)
                
            unbalanced_txs = []
            
            # Flush the current matched transaction
            amt_str = f"{amt:.2f}"
            if is_credit: amt_str += " CR"
            
            # If line 2 repeats description exactly from line 1, we can skip desc or keep it?
            # Actually, the user wants both distinct transactions to show up.
            row = f"{current_date} {desc_part} {amt_str}"
            transactions.append(row)
            print("Flushed (Anchored):", row)
            
        prev_balance = current_balance
        continue

    if single_amt_match:
        # It's an unbalanced tx (has amount, no balance)
        if date_match:
            current_date = date_match.group(1).strip()
            desc_part = line_str[date_match.end():single_amt_match.start()].strip()
        else:
            desc_part = line_str[:single_amt_match.start()].strip()
            
        amt = float(single_amt_match.group(1).replace(',', ''))
        unbalanced_txs.append({"date": current_date, "desc": desc_part, "abs_amount": amt})
        continue

    # Pure description lines (no amounts at all)
    # E.g. a multi-line description without amounts.
    # If we have unbalanced_txs pending, where should we append it?
    # Probably to the LAST unbalanced tx's description.
    if unbalanced_txs:
        if line_str and line_str not in unbalanced_txs[-1]["desc"]:
            unbalanced_txs[-1]["desc"] += " " + line_str
    else:
        # Or to a standard pending_tx if we brought that back.
        # In RBC Chequing, descriptions usually are on the same line as amounts.
        pass

print("\nFinal Extracted:")
for t in transactions:
    print(t)
