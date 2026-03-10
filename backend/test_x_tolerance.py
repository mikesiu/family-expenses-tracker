import pdfplumber

def check_bmo(pdf_path):
    print("Testing:", pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        print("====== DEFAULT ======")
        text = pdf.pages[0].extract_text()
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if "Opening" in line or "Perform" in line or "Jan" in line:
                print(f"{i}: {line}")
                
        print("\n====== x_tolerance=2 ======")
        text = pdf.pages[0].extract_text(x_tolerance=2)
        lines = text.split('\n')
        for i, line in enumerate(lines):
             if "Opening" in line or "Perform" in line or "Jan" in line:
                print(f"{i}: {line}")

if __name__ == "__main__":
    import sys
    # assuming the user's uploaded file might still be in a temp state, 
    # but we can't access it. At least we can verify it doesn't crash on standard files.
    print("Test script ready")
