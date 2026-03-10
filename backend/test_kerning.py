import pdfplumber
import sys

def test_tolerance(pdf_path):
    print(f"Testing {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print("--- x_tolerance=1 ---")
            print(pdf.pages[0].extract_text(x_tolerance=1, y_tolerance=2)[:1000])
            print("\n--- x_tolerance=1.5 ---")
            print(pdf.pages[0].extract_text(x_tolerance=1.5, y_tolerance=2)[:1000])
            print("\n--- x_tolerance=2 ---")
            print(pdf.pages[0].extract_text(x_tolerance=2, y_tolerance=2)[:1000])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_tolerance(sys.argv[1])
    else:
        print("Pass PDF path as argument.")
