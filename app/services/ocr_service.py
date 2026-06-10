"""
OCR Service Layer for MCU Vault.

Provides OCR extraction from PDF and image files.
Uses pytesseract for image-based OCR and pdf2image for PDF conversion.
"""

import os
import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR extraction."""
    success: bool
    text: str
    confidence: float
    pages_processed: int
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'text': self.text,
            'confidence': self.confidence,
            'pages_processed': self.pages_processed,
            'error_message': self.error_message
        }


class OCRService:
    """
    OCR Service for extracting text from MCU reports.
    Supports PDF, JPG, JPEG, and PNG formats.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR service.
        
        Args:
            tesseract_path: Optional path to tesseract executable
        """
        self.tesseract_path = tesseract_path
        self._tesseract_available = None
        self._poppler_available = None
    
    @property
    def tesseract_available(self) -> bool:
        """Check if tesseract OCR is available."""
        if self._tesseract_available is None:
            try:
                import pytesseract
                if self.tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
            except Exception:
                self._tesseract_available = False
        return self._tesseract_available
    
    @property
    def poppler_available(self) -> bool:
        """Check if poppler (for PDF processing) is available."""
        if self._poppler_available is None:
            try:
                from pdf2image import convert_from_path
                self._poppler_available = True
            except Exception:
                self._poppler_available = False
        return self._poppler_available
    
    def extract_from_image(self, image_path: str) -> OCRResult:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            OCRResult with extracted text and confidence
        """
        if not self.tesseract_available:
            return OCRResult(
                success=False,
                text='',
                confidence=0.0,
                pages_processed=0,
                error_message='Tesseract OCR is not installed. Please install tesseract-ocr.'
            )
        
        try:
            import pytesseract
            from PIL import Image
            
            # Open and process image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary (for RGBA images)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # Perform OCR with configuration for medical documents
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(
                image,
                config=custom_config,
                lang='eng'
            )
            
            # Calculate confidence based on text quality
            confidence = self._calculate_confidence(text)
            
            return OCRResult(
                success=True,
                text=text.strip(),
                confidence=confidence,
                pages_processed=1
            )
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return OCRResult(
                success=False,
                text='',
                confidence=0.0,
                pages_processed=0,
                error_message=str(e)
            )
    
    def extract_from_pdf(self, pdf_path: str) -> OCRResult:
        """
        Extract text from a PDF file.
        Converts PDF pages to images and performs OCR on each page.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            OCRResult with extracted text and confidence
        """
        if not self.tesseract_available:
            return OCRResult(
                success=False,
                text='',
                confidence=0.0,
                pages_processed=0,
                error_message='Tesseract OCR is not installed. Please install tesseract-ocr.'
            )
        
        if not self.poppler_available:
            return OCRResult(
                success=False,
                text='',
                confidence=0.0,
                pages_processed=0,
                error_message='PDF processing is not available. Please install poppler-utils.'
            )
        
        try:
            from pdf2image import convert_from_path
            
            # Convert PDF pages to images
            images = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=None,
                last_page=None
            )
            
            all_text = []
            total_confidence = 0.0
            pages_processed = 0
            
            import pytesseract
            
            for page_num, image in enumerate(images, 1):
                # Perform OCR on each page
                custom_config = r'--oem 3 --psm 6'
                page_text = pytesseract.image_to_string(
                    image,
                    config=custom_config,
                    lang='eng'
                )
                
                if page_text.strip():
                    all_text.append(f"--- Page {page_num} ---\n{page_text.strip()}")
                    total_confidence += self._calculate_confidence(page_text)
                    pages_processed += 1
            
            combined_text = '\n\n'.join(all_text)
            avg_confidence = total_confidence / pages_processed if pages_processed > 0 else 0.0
            
            return OCRResult(
                success=pages_processed > 0,
                text=combined_text,
                confidence=avg_confidence,
                pages_processed=pages_processed
            )
            
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {str(e)}")
            return OCRResult(
                success=False,
                text='',
                confidence=0.0,
                pages_processed=0,
                error_message=str(e)
            )
    
    def extract(self, file_path: str) -> OCRResult:
        """
        Extract text from any supported file type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            OCRResult with extracted text and confidence
        """
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.pdf':
            return self.extract_from_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png']:
            return self.extract_from_image(file_path)
        else:
            return OCRResult(
                success=False,
                text='',
                confidence=0.0,
                pages_processed=0,
                error_message=f'Unsupported file type: {ext}'
            )
    
    def _calculate_confidence(self, text: str) -> float:
        """
        Calculate confidence score based on text quality.
        
        Args:
            text: Extracted text
            
        Returns:
            Confidence score between 0 and 100
        """
        if not text:
            return 0.0
        
        # Base score starts at 70
        score = 70.0
        
        # Boost for longer text (more content extracted)
        word_count = len(text.split())
        if word_count > 50:
            score += 10
        elif word_count > 100:
            score += 15
        
        # Check for common OCR error patterns
        error_patterns = [
            (r'[\|_]', -5),  # Common OCR misreads
            (r'\s{2,}', -3),  # Multiple spaces
            (r'[0-9]{4,}', 5),  # Numbers likely correct
        ]
        
        for pattern, adjustment in error_patterns:
            import re
            if re.search(pattern, text):
                score += adjustment
        
        # Ensure score is within bounds
        return max(0.0, min(100.0, score))
    
    def is_available(self) -> bool:
        """Check if OCR service is available."""
        return self.tesseract_available


# Global OCR service instance
ocr_service = OCRService()


def extract_text(file_path: str) -> OCRResult:
    """
    Convenience function to extract text from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        OCRResult with extracted text and confidence
    """
    return ocr_service.extract(file_path)