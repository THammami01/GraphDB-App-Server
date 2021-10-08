import os
from docx2pdf import convert

# ! EACH FUNCTION HAS ONE PARAM THAT REPRESENTS THE FILE OF THE FILE TO CONVERT
# ! EACH FUNCTION MUST RETURN THE PATH OF THE RESULTING CONVERTED FILE

def convert_docx_to_pdf(file_path: str):
    filename, _ = os.path.splitext(file_path)
    pdf_file_path = f"{filename}.pdf"
    convert(file_path, pdf_file_path)
    return pdf_file_path
