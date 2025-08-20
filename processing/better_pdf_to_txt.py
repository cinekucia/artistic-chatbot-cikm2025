import fitz
import os

# Function to convert a PDF to a text file
def pdf_to_text(pdf_path, txt_path):
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    # Create a text file to store the extracted text
    with open(txt_path, "w", encoding="utf-8") as text_file:
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            text = page.get_text()
            text_file.write(text)
    
    # Close the PDF
    pdf_document.close()

# Directory paths
input_folder = "../data/pdf"
output_folder = "../data/output"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Loop through all files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(input_folder, filename)
        txt_filename = filename.replace(".pdf", ".txt")
        txt_path = os.path.join(output_folder, txt_filename)
        
        # Convert the PDF to a text file
        pdf_to_text(pdf_path, txt_path)

print("PDF to text conversion completed for all files.")
