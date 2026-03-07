import re

bmo_lines = [
    "Owners:",
    "Dec 25 Opening balance  5,554.35",
    "Dec 31 Performance Plan Fee 17.95 5,536.40",
    "Dec 31 Performance Plan Fee 17.95 5,554.35",
    "Jan 16 INTERAC e-Transfer Received 2,500.00 8,054.35",
    "Jan 21 Scheduled Transfer, TF 0005191230214007339 2,864.67 3,682.07",
    "Jan 21 INTERAC e-Transfer Received 2,000.00 5,682.07",
    "Jan 23 Pre-Authorized Payment, ROGERS PAC 203.81 5,478.26"
]

transactions = []
prev_balance = None

for line in bmo_lines:
    if "Opening balance" in line:
        bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line.strip())
        if bal_match:
            prev_balance = float(bal_match.group(1).replace(',', ''))
            print(f"Opening balance detected: {prev_balance}")

    date_match = re.match(r'^(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line.strip(), re.IGNORECASE)
    if date_match:
        bmo_cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line.strip())
        
        if bmo_cheq_match:
            stripped_line = line[:bmo_cheq_match.start(2)].strip()
            current_balance = float(bmo_cheq_match.group(2).replace(',', ''))
            tx_amount = float(bmo_cheq_match.group(1).replace(',', ''))
            
            if prev_balance is not None:
                if current_balance > prev_balance + 0.01:
                    stripped_line += " CR"
            
            prev_balance = current_balance
            print(f"Parsed row: {stripped_line}")
