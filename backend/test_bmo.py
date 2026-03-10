import re

bmo_lines = [
    "Dec 25 Opening balance 5,554.35",
    "Dec 31 Performance Plan Fee 17.95 5,536.40",
    "Jan 16 INTERAC e-Transfer Received 2,500.00 8,054.35",
    "Jan 19 Debit Card Purchase, SANBO CHINESE RESTAURN 70.15 7,984.20",
    "Jan 21 Scheduled Transfer, TF 0005191230214007339 2,864.67 3,682.07",
    "Jan 23 Pre-Authorized Payment, ROGERS PAC BPY/FAC 203.81 5,478.26"
]

transactions = []
prev_balance = None
account_type = "Chequing"

for line in bmo_lines:
    line_str = line.strip()
    
    if "Opening balance" in line_str or "balance forward" in line_str.lower():
        bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
        if bal_match:
            prev_balance = float(bal_match.group(1).replace(',', ''))
            print("Set prev_balance:", prev_balance)
        continue
        
    date_match = re.match(r'^\s*(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line_str, re.IGNORECASE)
    
    if date_match:
        bmo_cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
        
        if account_type == "Chequing" and bmo_cheq_match:
            stripped_line = line_str[:bmo_cheq_match.start(2)].strip()
            
            try:
                current_balance = float(bmo_cheq_match.group(2).replace(',', ''))
                tx_amount = float(bmo_cheq_match.group(1).replace(',', ''))
            except Exception as e:
                print("Error parsing amounts:", e)
                continue
            
            amt_str = f"{tx_amount:.2f}"
            if prev_balance is not None:
                if current_balance > prev_balance + 0.01:
                    amt_str += " CR"
            
            prev_balance = current_balance
            raw_row = stripped_line.split()[: -len(bmo_cheq_match.group(0).split())] + [amt_str]
            print("Extracted row:", raw_row)
