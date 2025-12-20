"""
PDF Processor - Converts multi-page PDFs to image arrays for VisionEngine
"""
import io
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    convert_from_bytes = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

class PDFProcessor:
    """
    Processes multi-page PDFs by converting to image arrays.
    """
    
    def __init__(self):
        if not PDF2IMAGE_AVAILABLE:
            logger.warning("pdf2image not available. Install with: pip install pdf2image")
        if not PIL_AVAILABLE:
            logger.warning("PIL not available. Install with: pip install pillow")
    
    def is_pdf(self, file_data: bytes) -> bool:
        """
        Check if file data is a PDF.
        
        Args:
            file_data: File bytes
        
        Returns:
            True if PDF, False otherwise
        """
        return file_data[:4] == b'%PDF'
    
    def pdf_to_images(self, pdf_data: bytes, dpi: int = 200) -> List[bytes]:
        """
        Convert PDF pages to image bytes.
        
        Args:
            pdf_data: PDF file bytes
            dpi: Resolution for conversion (default: 200)
        
        Returns:
            List of image bytes (one per page)
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image not installed. Run: pip install pdf2image")
        
        if not PIL_AVAILABLE:
            raise ImportError("PIL not installed. Run: pip install pillow")
        
        try:
            # Convert PDF pages to PIL Images
            images = convert_from_bytes(pdf_data, dpi=dpi)
            
            # Convert PIL Images to bytes
            image_bytes_list = []
            for img in images:
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                image_bytes_list.append(img_bytes.getvalue())
            
            logger.info(f"Converted PDF to {len(image_bytes_list)} pages")
            return image_bytes_list
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to convert PDF to images: {str(e)}")
    
    def get_page_count(self, pdf_data: bytes) -> int:
        """
        Get number of pages in PDF without converting.
        
        Args:
            pdf_data: PDF file bytes
        
        Returns:
            Number of pages
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image not installed")
        
        try:
            images = convert_from_bytes(pdf_data, first_page=1, last_page=1)
            # This is a workaround - we convert first page to get count
            # In production, use PyPDF2 for faster page counting
            from pdf2image import pdfinfo_from_bytes
            info = pdfinfo_from_bytes(pdf_data)
            return info.get('Pages', 1)
        except Exception as e:
            logger.warning(f"Could not get page count: {e}, assuming 1 page")
            return 1

