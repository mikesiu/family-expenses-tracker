import re

cibc_lines = [
    "2026-01-01 Opening balance $ 9509.82",
    "2026-01-02 E-TRANSFER 105766138648 65.00 9444.82",
    "2026-01-05 RETAIL PURCHASE 000001089229 57.36 8946.78",
    "2026-01-06 E-TRANSFER 105772351465 100.00 9002.18",
    "2026-01-08 PREAUTHORIZED DEBIT 3,227.20 5774.98"
]

transactions = []
prev_balance = None

for line in cibc_lines:
    if "Opening balance" in line:
        bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line.strip())
        if bal_match:
            prev_balance = float(bal_match.group(1).replace(',', ''))
            print(f"Opening balance detected: {prev_balance}")

    date_match = re.match(r'^\s*(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line, re.IGNORECASE)
    if date_match and "Opening balance" not in line:
        # Match two amounts at end for chequing
        cibc_cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line.strip())
        # Match one amount at end for credit
        cibc_cred_match = re.search(r'(-?[\d,]+[.,]\d{2})(?:\s*CR)?$', line.strip(), re.IGNORECASE)
        
        if cibc_cheq_match:
            stripped_line = line[:cibc_cheq_match.start(2)].strip()
            current_balance = float(cibc_cheq_match.group(2).replace(',', ''))
            tx_amount = float(cibc_cheq_match.group(1).replace(',', ''))
            
            if prev_balance is not None:
                if current_balance > prev_balance + 0.01:
                    stripped_line += " CR"
            
            prev_balance = current_balance
            print(f"Parsed CIBC Cheq: {stripped_line}")
        elif cibc_cred_match:
            print(f"Parsed CIBC Cred: {line}")
