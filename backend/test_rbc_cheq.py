import re

text_lines = [
    "Details of your account activity",
    "Date Description Withdrawals ($) Deposits ($) Balance ($)",
    "Opening Balance 23,786.62",
    "2 Jan Deposit interest 11.61 23,798.23",
    "19 Jan Online Transfer to Deposit Account-8941 2,000.00 21,798.23",
    "Closing Balance $21,798.23"
]

transactions = []
current_date = None
pending_tx = None

# Similar to RBC Credit, but single date 'D MMM' or 'DD MMM'
# Then we have potentially 2 amounts at the end ? 
# "2 Jan Deposit interest 11.61 23,798.23" -> (amount) (balance)
# "19 Jan Online Transfer to Deposit Account-8941 2,000.00 21,798.23" -> (amount) (balance)

# To tell if it's withdrawal or deposit, we can check if it aligns with the column? Too hard in pdfplumber text.
# Let's track prev_balance instead!
prev_balance = None

def flush_tx():
    global pending_tx, current_date, transactions
    if pending_tx and current_date:
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
            print("Set prev_balance:", prev_balance)
        continue

    # Filter headers
    if re.search(r'(^Details of your account|^Summary of your account|Your opening balance|Total deposits|Total withdrawals|Your closing balance|^Date\s+Description|Closing Balance|Important information)', line_str, re.IGNORECASE):
        flush_tx()
        pending_tx = None
        current_date = None
        continue

    # Date match: 2 Jan or 19 Jan
    date_match = re.match(r'^(\d{1,2}\s+[A-Z][a-z]{2}\.?|\d{1,2}\s+[A-Z]{3})\b', line_str, re.IGNORECASE)
    
    # RBC savings/chequing has Amount and Balance at the end
    cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
    
    if date_match and cheq_match:
        flush_tx()
        pending_tx = None
        current_date = date_match.group(1).strip()
        
        desc_part = line_str[date_match.end():cheq_match.start()].strip()
        
        tx_amt = float(cheq_match.group(1).replace(',', ''))
        current_balance = float(cheq_match.group(2).replace(',', ''))
        
        amt_str = f"{tx_amt:.2f}"
        if prev_balance is not None:
            if current_balance > prev_balance + 0.01:
                amt_str += " CR"
        prev_balance = current_balance
        
        pending_tx = {"desc_words": [desc_part], "amount": amt_str}
    else:
        if pending_tx:
            pending_tx["desc_words"].append(line_str)

flush_tx()
