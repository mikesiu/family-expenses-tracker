import re

def _parse_bmo(text_lines, account_type="Chequing"):
    transactions = []
    prev_balance = None
    current_date = None
    pending_tx = None
    
    def flush_tx():
        if pending_tx and current_date:
            raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
            transactions.append({"raw_row": raw_row_str.split()})
            print(f"Flushed: {raw_row_str}")
            
    for line in text_lines:
        line_str = line.strip()
        if not line_str: continue
        
        # Handle Explicit Opening Balance text if it exists
        if "Opening balance" in line_str or "balance forward" in line_str.lower():
            bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
            if bal_match:
                prev_balance = float(bal_match.group(1).replace(',', ''))
                print("Found prev_balance:", prev_balance)
            continue
        
        # Filter headers
        if re.search(r'(^Total|^Your everyday|^Summary of your account|Amounts deducted|Amounts added|Balance \(|Page \d+ of|Account number:|Important:|Branch transit number:|Your rights under|Please check this statement|authorized signature|For more information|Trademarks)', line_str, re.IGNORECASE):
            print("Filtered header:", line_str)
            flush_tx()
            pending_tx = None
            current_date = None
            continue
        
        date_match = re.match(r'^(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line_str, re.IGNORECASE)
        
        bmo_cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
        bmo_cred_match = re.search(r'(-?[\d,]+[.,]\d{2})(?:\s*CR)?$', line_str, re.IGNORECASE)
        
        has_amount = False
        is_cheq = False
        amt_match = None
        
        if account_type == "Chequing" and bmo_cheq_match:
            has_amount = True
            is_cheq = True
            amt_match = bmo_cheq_match
        elif account_type != "Chequing" and bmo_cred_match:
            has_amount = True
            is_cheq = False
            amt_match = bmo_cred_match
            
        if has_amount:
            # New transaction, flush previous
            flush_tx()
            pending_tx = None
            
            if date_match:
                current_date = date_match.group(0).strip()
                line_str = line_str[date_match.end():].strip()
                
            if not current_date:
                continue
                
            if is_cheq:
                desc_part = line_str[:line_str.rfind(amt_match.group(0))].strip()
                current_balance = float(amt_match.group(2).replace(',', ''))
                tx_amount = float(amt_match.group(1).replace(',', ''))
                
                amt_str = f"{tx_amount:.2f}"
                if prev_balance is not None:
                    if current_balance > prev_balance + 0.01:
                        amt_str += " CR"
                prev_balance = current_balance
                
                pending_tx = {"desc_words": [desc_part] if desc_part else [], "amount": amt_str}
            else:
                desc_part = line_str[:line_str.rfind(amt_match.group(0))].strip()
                pending_tx = {"desc_words": [desc_part] if desc_part else [], "amount": amt_match.group(0)}
        else:
            # Append desc
            if pending_tx:
                pending_tx["desc_words"].append(line_str)
                
    flush_tx()
    return transactions

lines = [
    "Your Everyday Banking statement",
    "For the period ending January 23, 2026",
    "Summary of your account",
    "Primary Chequing Account # 0760 3919-325 5,554.35 4,636.05 4,517.95 5,436.25",
    "Here's what happened in your account",
    "Amounts deducted from your account ($) Amounts added to your account ($) Balance ($)",
    "Dec 25 Opening balance 5,554.35",
    "Dec 31 Performance Plan Fee 17.95 5,536.40",
    "Dec 31 Performance Plan Fee 17.95 5,554.35",
    "Jan 16 INTERAC e-Transfer Received 2,500.00 8,054.35"
]

_parse_bmo(lines)
