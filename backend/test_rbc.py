import re

text_lines = [
    "DEC 19 DEC 24 PAYPAL *TSC 4029357733 ON $55.99",
    "85121645357550383139680",
    "DEC 22 DEC 24 PAYPAL *UBER 4029357733 ON $23.84",
    "85121645357550384679577",
    "JAN 02 JAN 02 PAYMENT - THANK YOU / PAIEMENT - MERCI -$745.73",
    "75105396002619988607407",
    "JAN 04 JAN 05 CASH BACK REWARD -$114.81",
    "10692328527",
    "JAN 07 JAN 09 PAYPAL *FEDEXCANADA 4029357733 ON $29.87",
    "85121646008601411874052",
    "JAN 09 JAN 12 PAYPAL *PATREON MEMBE 4029357733 CA $8.10",
    "82147126009601049115075",
]

transactions = []
current_date = None
pending_tx = None

def flush_tx():
    global pending_tx, current_date, transactions
    if pending_tx and current_date:
        raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
        transactions.append({"raw_row": raw_row_str.split()})
        print("Flushed:", raw_row_str)

for line in text_lines:
    line_str = line.strip()
    if not line_str: continue
    
    # Matches: MMM DD MMM DD
    date_match = re.match(r'^([A-Z][a-z]{2}\.?\s+\d{1,2}|[A-Z]{3}\s+\d{1,2})\s+([A-Z][a-z]{2}\.?\s+\d{1,2}|[A-Z]{3}\s+\d{1,2})', line_str, re.IGNORECASE)
    
    # Amount match at the end: e.g. $55.99 or -$745.73
    amt_match = re.search(r'(-?\$?[\d,]+[.,]\d{2})(?:\s*CR)?$', line_str, re.IGNORECASE)
    
    if amt_match and date_match:
        flush_tx()
        pending_tx = None
        
        current_date = date_match.group(1).strip()
        # line without dates and without amounts
        desc_part = line_str[date_match.end():line_str.rfind(amt_match.group(0))].strip()
        
        amt_val_str = amt_match.group(1).replace('$', '').replace(',', '')
        
        # Credit cards: negative amounts are payments (CR), positive are purchases. 
        # But for DB, we want purchases as negative, payments as positive. Wait, how is main.py handling amounts?
        # Let's just output the exact string, e.g. "55.99" or "745.73 CR", or "-745.73" and let main.py parse it.
        # Actually main.py parses negative as expense (if not CR). So if it's "-745.73", it parses as -745.73. 
        # But -$745.73 is a PAYMENT. A payment in credit card is a credit (reduces balance). 
        # Wait, the RBC statement says `PAYMENT ... -$745.73`. That means it's a credit.
        # Let's convert "-$745.73" to "745.73 CR" to match the CR flow which main.py knows is positive.
        if amt_val_str.startswith('-'):
            amt_val_str = amt_val_str[1:] + " CR"
            
        pending_tx = {"desc_words": [desc_part] if desc_part else [], "amount": amt_val_str}
    else:
        if pending_tx:
            pending_tx["desc_words"].append(line_str)

flush_tx()
