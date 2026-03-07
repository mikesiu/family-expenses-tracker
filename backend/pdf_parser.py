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
        elif "bmo" in text_lower or "bank of montreal" in text_lower:
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

    def parse(self) -> Dict[str, Any]:
        extracted_data = []
        full_bank_name = "Unknown"
        
        with pdfplumber.open(self.file_path) as pdf:
            if not pdf.pages:
                return {"bank_name": full_bank_name, "transactions": []}
                
            first_page_text = pdf.pages[0].extract_text()
            bank_name = self.detect_bank(first_page_text)
            card_type = self.detect_card_type(first_page_text)
            
            full_bank_name = f"{bank_name} {card_type}".strip()
            
            # Switch parser based on bank
            if bank_name == "CIBC":
                extracted_data = self._parse_cibc(pdf)
            elif bank_name == "BMO":
                extracted_data = self._parse_bmo(pdf)
            elif bank_name == "RBC":
                extracted_data = self._parse_rbc(pdf)
            elif bank_name == "TD":
                extracted_data = self._parse_td(pdf)
            elif bank_name == "Scotiabank":
                extracted_data = self._parse_scotiabank(pdf)
            else:
                raise ValueError("Could not detect a supported bank format.")
                
        return {"bank_name": full_bank_name, "transactions": extracted_data}

    # Placeholder parsers - actual logic requires manual review of each bank's PDF structure
    # A generic table extractor is used as a fallback/starting point
    
    def _parse_generic_table(self, pdf) -> List[Dict]:
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

    def _parse_cibc(self, pdf) -> List[Dict[str, Any]]:
        transactions = []
        parsing_started = False
        
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                # CIBC Headers
                if "Transactions from" in line or "TRANSACTIONS" in line or "Your payments" in line or "Your new charges" in line:
                    parsing_started = True
                    continue
                    
                if parsing_started:
                    # Line must end with a decimal amount (e.g. 123.45 or 123.45 CR)
                    if re.search(r'\d+[.,]\d{2}(?:\s*CR)?$', line.strip(), re.IGNORECASE):
                        # Line must start with a date-like pattern (e.g. Dec. 3, 2026-03-04, 12/25)
                        if re.match(r'^(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line.strip(), re.IGNORECASE):
                            parts = line.split()
                            transactions.append({"raw_row": parts})
                            
        return transactions

    def _parse_bmo(self, pdf) -> List[Dict[str, Any]]:
        transactions = []
        parsing_started = False
        prev_balance = None
        
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                # Handle Explicit Opening Balance text if it exists
                if "Opening balance" in line:
                    bal_match = re.search(r'(-?[\d,]+[.,]\d{2})$', line.strip())
                    if bal_match:
                        prev_balance = float(bal_match.group(1).replace(',', ''))
                
                if "what happened in your account" in line.lower() or "transactions" in line.lower() or "transaction details" in line.lower():
                    parsing_started = True
                    continue
                    
                if parsing_started:
                    date_match = re.match(r'^(?:[A-Z][a-z]{2}\.?\s+\d{1,2}|\d{2,4}[-/]\d{1,2}[-/]\d{1,4}|\d{1,2}/\d{1,2}|\d{1,2}\s+[A-Z][a-z]{2})', line.strip(), re.IGNORECASE)
                    if date_match:
                        # BMO Chequing has two amounts at the end: [Transaction Amount] [Balance]
                        bmo_cheq_match = re.search(r'(-?[\d,]+[.,]\d{2})\s+(-?[\d,]+[.,]\d{2})$', line.strip())
                        # BMO Credit card has one amount
                        bmo_cred_match = re.search(r'(-?[\d,]+[.,]\d{2})(?:\s*CR)?$', line.strip(), re.IGNORECASE)
                        
                        if bmo_cheq_match:
                            # Strip the balance off the end
                            stripped_line = line[:bmo_cheq_match.start(2)].strip()
                            
                            current_balance = float(bmo_cheq_match.group(2).replace(',', ''))
                            tx_amount = float(bmo_cheq_match.group(1).replace(',', ''))
                            
                            if prev_balance is not None:
                                # Determine if it was added or deducted
                                # Due to rounding, allow small epsilon
                                if current_balance > prev_balance + 0.01:
                                    stripped_line += " CR"
                            
                            prev_balance = current_balance
                            transactions.append({"raw_row": stripped_line.split()})
                            
                        elif bmo_cred_match:
                            transactions.append({"raw_row": line.split()})
                            
        return transactions

    def _parse_rbc(self, pdf) -> List[Dict[str, Any]]:
         # TODO: Implement accurate RBC table parsing
        return self._parse_generic_table(pdf)

    def _parse_td(self, pdf) -> List[Dict[str, Any]]:
         # TODO: Implement accurate TD table parsing
        return self._parse_generic_table(pdf)

    def _parse_scotiabank(self, pdf) -> List[Dict[str, Any]]:
         # TODO: Implement accurate Scotiabank table parsing
        return self._parse_generic_table(pdf)
