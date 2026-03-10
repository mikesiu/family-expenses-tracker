import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Any

class PDFParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def detect_bank(self, text: str) -> str:
        """
        Detects the bank based on keywords in the first page of the PDF.
        """
        text_lower = text.lower()
        if "cibc" in text_lower:
            return "CIBC"
        elif "bmo" in text_lower or "bank of montreal" in text_lower or "everyday banking" in text_lower:
            return "BMO"
        elif "rbc" in text_lower or "royal bank" in text_lower:
            return "RBC"
        elif "td" in text_lower or "toronto dominion" in text_lower:
            return "TD"
        elif "scotia" in text_lower or "scotiabank" in text_lower:
            return "Scotiabank"
        return "Unknown"

    def detect_card_type(self, text: str) -> str:
        """
        Detects the credit card type based on keywords in the first page.
        """
        text_lower = text.lower()
        if "mastercard" in text_lower:
            return "Mastercard"
        elif "visa" in text_lower:
            return "Visa"
        elif "american express" in text_lower or "amex" in text_lower:
            return "Amex"
        return ""

    def detect_account_type(self, text: str, card_type: str) -> str:
        """
        Detects if the document is for a Chequing, Savings, or Credit Card account.
        """
        text_lower = text.lower()
        if card_type or "credit card" in text_lower or "mastercard" in text_lower or "visa" in text_lower:
            return "Credit Card"
        elif "savings" in text_lower or "épargne" in text_lower:
            return "Savings"
        return "Chequing" # Default to Chequing if no clear saving or credit markers

    def parse(self) -> Dict[str, Any]:
        extracted_data = []
        full_bank_name = "Unknown"
        
        with pdfplumber.open(self.file_path) as pdf:
            if not pdf.pages:
                return {"bank_name": full_bank_name, "transactions": []}
                
            first_page_text = str(pdf.pages[0].extract_text() or "")
            
            print("\n" + "="*50)
            print("DEBUG: FIRST PAGE TEXT DUMP (First 1000 chars):")
            print(first_page_text[:1000])
            print("="*50 + "\n")
            
            bank_name = self.detect_bank(first_page_text)
            card_type = self.detect_card_type(first_page_text)
            account_type = self.detect_account_type(first_page_text, card_type)
            
            print(f"DEBUG: Detected Bank: '{bank_name}'")
            print(f"DEBUG: Detected Card: '{card_type}'")
            print(f"DEBUG: Detected Account Type: '{account_type}'")
            
            full_bank_name = f"{bank_name} {card_type}".strip()
            
            # Switch parser based on bank
            if bank_name == "CIBC":
                extracted_data = self._parse_cibc(pdf, account_type)
            elif bank_name == "BMO":
                extracted_data = self._parse_bmo(pdf, account_type)
            elif bank_name == "RBC":
                extracted_data = self._parse_rbc(pdf, account_type)
            elif bank_name == "TD":
                extracted_data = self._parse_td(pdf, account_type)
            elif bank_name == "Scotiabank":
                extracted_data = self._parse_scotiabank(pdf, account_type)
            else:
                extracted_data = self._parse_generic_table(pdf, account_type)
                
            if not extracted_data:
                print("DEBUG: Custom engines extracted 0 transactions. Falling back to Generic Filter...")
                extracted_data = self._parse_generic_table(pdf, account_type)
                
            years_found = sorted(list(set(re.findall(r'(202[0-9])', first_page_text))))
            if not years_found:
                years_found = [str(datetime.now().year)]
                
        print(f"DEBUG: Extraction complete. Total row items: {len(extracted_data)}")
        return {"bank_name": full_bank_name, "account_type": account_type, "transactions": extracted_data, "statement_years": [int(y) for y in years_found]}

    # Placeholder parsers - actual logic requires manual review of each bank's PDF structure
    # A generic table extractor is used as a fallback/starting point
    
    def _parse_generic_table(self, pdf, account_type: str = "Chequing") -> List[Dict]:
        """A generic text-based parser attempt for unknown precise formats."""
        transactions = []
        parsing_started = False
        
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                # Start extracting after recognizing common headers
                if "Transactions since your last statement" in line or "TRANSACTIONS" in line or "Transaction Details" in line:
                    parsing_started = True
                    continue
                    
                if parsing_started:
                    # Line must end with a decimal amount (e.g. 123.45 or 123.45 CR)
                    if re.search(r'\d+[.,]\d{2}(?:\s*CR)?$', line.strip(), re.IGNORECASE):
                        # Line must start with a date-like pattern (e.g. Dec. 3, 2026-03-04, 12/25).
                        # Using \s* to handle smashed dates like 'Dec. 10Dec. 10'
                        if re.match(r'^(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line.strip(), re.IGNORECASE):
                            parts = line.split()
                            transactions.append({"raw_row": parts})
                    
        return transactions

    def _parse_cibc(self, pdf, account_type: str = "Chequing") -> List[Dict[str, Any]]:
        transactions = []
        prev_balance = None
        current_date = None
        pending_tx = None
        
        def flush_tx():
            if pending_tx and current_date:
                raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
                transactions.append({"raw_row": raw_row_str.split()})
                
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                line_str = line.strip()
                if not line_str: continue
                
                # Handle Explicit Opening Balance text if it exists
                if "Opening balance" in line_str or "balance forward" in line_str.lower():
                    bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
                    if bal_match:
                        prev_balance = float(bal_match.group(1).replace(',', ''))
                    continue
                
                # Filter headers
                if re.search(r'(^Total|^Your payments|^Your new charges|^Spend Categories|Withdrawals|Deposits|Balance|Transaction details|Closing balance|Page \d+ of|Account number:|Important:|Branch transit number:|Your rights under|Please check this statement|authorized signature|For more information|Trademarks)', line_str, re.IGNORECASE):
                    flush_tx()
                    pending_tx = None
                    current_date = None
                    continue
                
                date_match = re.match(r'^(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line_str, re.IGNORECASE)
                
                cibc_cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
                cibc_cred_match = re.search(r'(-?[\d,]+[.,]\d{2})(?:\s*CR)?$', line_str, re.IGNORECASE)
                
                has_amount = False
                is_cheq = False
                amt_match = None
                
                if account_type == "Chequing" and cibc_cheq_match:
                    has_amount = True
                    is_cheq = True
                    amt_match = cibc_cheq_match
                elif account_type != "Chequing" and cibc_cred_match:
                    has_amount = True
                    is_cheq = False
                    amt_match = cibc_cred_match
                    
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

    def _parse_bmo(self, pdf, account_type: str = "Chequing") -> List[Dict[str, Any]]:
        transactions = []
        prev_balance = None
        current_date = None
        pending_tx = None
        
        def flush_tx():
            if pending_tx and current_date:
                raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
                transactions.append({"raw_row": raw_row_str.split()})
                
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2)
            if not text:
                continue
            for line in text.split('\n'):
                line_str = line.strip()
                if not line_str: continue
                
                # Handle Explicit Opening Balance text if it exists
                if "Opening balance" in line_str or "balance forward" in line_str.lower():
                    bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
                    if bal_match:
                        prev_balance = float(bal_match.group(1).replace(',', ''))
                    continue
                
                # Filter headers
                if re.search(r'(Total|^Your everyday|^Summary of your account|Amounts deducted|Amounts added|Balance \(|Page \d+ of|Account number:|Important:|Branch transit number:|Your rights under|Please check this statement|authorized signature|For more information|Trademarks)', line_str, re.IGNORECASE):
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

    def _parse_rbc(self, pdf, account_type: str = "Chequing") -> List[Dict[str, Any]]:
        transactions = []
        current_date = None
        pending_tx = None
        prev_balance = None
        unbalanced_txs = []
        
        def flush_tx():
            if pending_tx and current_date and "amount" in pending_tx:
                raw_row_str = f"{current_date} {' '.join(pending_tx['desc_words'])} {pending_tx['amount']}"
                transactions.append({"raw_row": raw_row_str.split()})
                
        for page in pdf.pages:
            if account_type not in ["Chequing", "Savings"]:
                # Crop to the left 57% of the page to surgically discard the right-hand summary column for Credit Cards
                crop_box = (0, 0, page.width * 0.575, page.height)
                cropped_page = page.crop(crop_box)
                text = cropped_page.extract_text(x_tolerance=2, y_tolerance=2)
            else:
                # Chequing/Savings use the full width of the page for their columns, x_tolerance=1 to fix spaces
                text = page.extract_text(x_tolerance=1, y_tolerance=2)
                
            if not text:
                continue
            for line in text.split('\n'):
                line_str = line.strip()
                if not line_str: continue
                
                # RBC Chequing: Handle Explicit Opening Balance
                if account_type in ["Chequing", "Savings"]:
                    if "Opening Balance" in line_str and not re.match(r'^\d{1,2}\s*[A-Za-z]{3}\b', line_str):
                        bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line_str)
                        if bal_match:
                            prev_balance = float(bal_match.group(1).replace(',', ''))
                        continue

                # Filter headers
                if re.search(r'(^PREVIOUS ACCOUNT BALANCE|^NEW BALANCE|^TOTAL ACCOUNT BALANCE|^PAYMENTS & INTEREST|^CASH BACK|STATEMENT FROM|IMPORTANT INFORMATION|Page \d+ of|Branch transit|^Details of your account|^Summary of your account|Your opening balance|Total deposits|Total withdrawals|Your closing balance|^Date\s+Description|Closing\s*Balance)', line_str, re.IGNORECASE):
                    flush_tx()
                    pending_tx = None
                    current_date = None
                    continue
                
                if account_type not in ["Chequing", "Savings"]:
                    # RBC CREDIT CARD PARSING
                    date_match = re.match(r'^([A-Z][a-z]{2}\.?\s*\d{1,2}|[A-Z]{3}\s*\d{1,2})\s+([A-Z][a-z]{2}\.?\s*\d{1,2}|[A-Z]{3}\s*\d{1,2})', line_str, re.IGNORECASE)
                    amt_match = re.search(r'(-?\$?[\d,]+[.,]\d{2})(?:\s*CR)?$', line_str, re.IGNORECASE)
                    
                    if date_match and amt_match:
                        flush_tx()
                        pending_tx = None
                        
                        current_date = date_match.group(1).strip()
                        desc_part = line_str[date_match.end():line_str.rfind(amt_match.group(0))].strip()
                        
                        amt_val_str = amt_match.group(1).replace('$', '').replace(',', '')
                        if amt_val_str.startswith('-'):
                            amt_val_str = amt_val_str[1:] + " CR"
                            
                        pending_tx = {"desc_words": [desc_part] if desc_part else [], "amount": amt_val_str}
                    else:
                        if pending_tx:
                            pending_tx["desc_words"].append(line_str)
                else:
                    # RBC CHEQUING/SAVINGS PARSING (Single date, dual amount ending)
                    date_match = re.match(r'^(\d{1,2}\s*[A-Z][a-z]{2}\.?|\d{1,2}\s*[A-Z]{3})\b', line_str, re.IGNORECASE)
                    cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line_str)
                    single_amt_match = re.search(r'\b(-?[\d,]+[.,]\d{2})$', line_str)
                    
                    if cheq_match:
                        # Line concluding with full balance resolves everything
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
                            
                            # Safely flush any unbalanced txs accumulated prior to this line
                            for utx in unbalanced_txs:
                                amt_str = f"{utx['abs_amount']:.2f}"
                                if is_credit: amt_str += " CR"
                                raw_row_str = f"{utx['date']} {' '.join(utx['desc_words'])} {amt_str}"
                                transactions.append({"raw_row": raw_row_str.split()})
                            unbalanced_txs = []
                            
                            amt_str = f"{amt:.2f}"
                            if is_credit: amt_str += " CR"
                            
                            flush_tx()
                            pending_tx = {"date": current_date, "desc_words": [desc_part] if desc_part else [], "amount": amt_str}
                            
                        prev_balance = current_balance
                        
                    elif single_amt_match:
                        # Missing balance? It's an unbalanced squashed tx.
                        flush_tx()
                        pending_tx = None
                        if date_match:
                            current_date = date_match.group(1).strip()
                            desc_part = line_str[date_match.end():single_amt_match.start()].strip()
                        else:
                            desc_part = line_str[:single_amt_match.start()].strip()
                            
                        amt = float(single_amt_match.group(1).replace(',', ''))
                        unbalanced_txs.append({"date": current_date, "desc_words": [desc_part] if desc_part else [], "abs_amount": amt})
                        
                    else:
                        # Pure description lines
                        if unbalanced_txs:
                            if line_str and line_str not in unbalanced_txs[-1]["desc_words"]:
                                unbalanced_txs[-1]["desc_words"].append(line_str)
                        elif pending_tx:
                            if line_str and line_str not in pending_tx["desc_words"]:
                                pending_tx["desc_words"].append(line_str)
                        
        flush_tx()
        return transactions

    def _parse_td(self, pdf, account_type: str = "Chequing") -> List[Dict[str, Any]]:
         # TODO: Implement accurate TD table parsing
        return self._parse_generic_table(pdf, account_type)

    def _parse_scotiabank(self, pdf, account_type: str = "Chequing") -> List[Dict[str, Any]]:
         # TODO: Implement accurate Scotiabank table parsing
        return self._parse_generic_table(pdf, account_type)
