"""
OCR module for InSitu vocabulary app.
Handles image-to-text extraction using pytesseract.
"""

from PIL import Image
import pytesseract
import io


def extract_text_from_image(uploaded_file) -> tuple[bool, str]:
    """
    Extract text from an uploaded image file using OCR.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        tuple: (success: bool, text_or_error: str)
    """
    try:
        # Read the image from the uploaded file
        image_bytes = uploaded_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles PNG with transparency)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Extract text using pytesseract
        extracted_text = pytesseract.image_to_string(image)
        
        # Clean up the text
        extracted_text = extracted_text.strip()
        
        if not extracted_text:
            return False, "No text could be extracted from this image. Please try a clearer image or paste the text manually."
        
        return True, extracted_text
        
    except pytesseract.TesseractNotFoundError:
        return False, (
            "Tesseract OCR is not installed on your system.\n\n"
            "**To install on macOS:**\n"
            "```\nbrew install tesseract\n```\n\n"
            "After installation, restart the app."
        )
    except Exception as e:
        return False, f"Error processing image: {str(e)}"


def is_tesseract_available() -> bool:
    """Check if Tesseract is available on the system."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except pytesseract.TesseractNotFoundError:
        return False
