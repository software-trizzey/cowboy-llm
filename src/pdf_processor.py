import PyPDF2
import io

def extract_text_from_pdf(pdf_file):
    """
    Extract text from a PDF file object
    """
    try:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return None 