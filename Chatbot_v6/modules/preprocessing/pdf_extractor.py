"""
PDF Extractor - PDF 텍스트 추출

PDF 파일에서 텍스트를 추출합니다 (단일 책임).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from modules.core.exceptions import PDFLoadError, TextExtractionError
from modules.core.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """
    PDF 텍스트 추출기
    
    단일 책임: PDF에서 텍스트 추출만 수행
    """
    
    def __init__(self):
        logger.debug("PDFExtractor initialized")
    
    def extract_text_from_file(self, file_path: str | Path) -> str:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
            
        Raises:
            PDFLoadError: PDF 로드 실패
            TextExtractionError: 텍스트 추출 실패
        """
        path = Path(file_path)
        
        if not path.exists():
            raise PDFLoadError(str(path), cause=FileNotFoundError(f"File not found: {path}"))
        
        if not path.suffix.lower() == ".pdf":
            raise PDFLoadError(str(path), cause=ValueError(f"Not a PDF file: {path}"))
        
        try:
            import pymupdf  # PyMuPDF
            
            logger.info(f"Extracting text from PDF: {path}")
            
            doc = pymupdf.open(str(path))
            
            pages_text = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pages_text.append(text)
                logger.debug(f"Extracted page {page_num + 1}/{len(doc)}", 
                            chars=len(text))
            
            doc.close()
            
            full_text = "\n\n".join(pages_text)
            
            logger.info(f"PDF extraction complete", 
                       pages=len(pages_text),
                       total_chars=len(full_text))
            
            # 텍스트가 비어있으면 OCR 시도
            if not full_text or full_text.strip() == "":
                logger.info(f"No text extracted from PDF - falling back to OCR: {path}")
                return self._extract_text_ocr(str(path))
            
            return full_text
        
        except ImportError as e:
            raise TextExtractionError(
                str(path),
                cause=ImportError("pymupdf not installed. Run: pip install pymupdf")
            ) from e
        
        except Exception as e:
            logger.warning(f"PDF text extraction failed, attempting OCR fallback: {path}")
            try:
                return self._extract_text_ocr(str(path))
            except Exception as ocr_error:
                raise TextExtractionError(
                    str(path),
                    cause=e,
                ) from e
    
    def _extract_text_ocr(self, file_path: str) -> str:
        """
        PDF를 OCR로 텍스트 추출 (fallback)
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
            
        Raises:
            TextExtractionError: OCR 추출 실패
        """
        try:
            import pytesseract
            from PIL import Image
            import pymupdf
            
            logger.info(f"Using Tesseract OCR for: {file_path}")
            
            doc = pymupdf.open(file_path)
            extracted_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 2x zoom for better OCR accuracy
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(img, lang='kor+eng')
                extracted_text += page_text + "\n\n"
                logger.debug(f"OCR extracted page {page_num + 1}/{len(doc)}", 
                            chars=len(page_text))
            
            doc.close()
            
            logger.info(f"OCR extraction complete", 
                       pages=len(doc),
                       total_chars=len(extracted_text))
            
            return extracted_text
        
        except ImportError as e:
            logger.error(f"Required OCR libraries not installed: pytesseract, Pillow", error_code="E402")
            raise TextExtractionError(
                file_path,
                cause=ImportError("pytesseract or Pillow not installed. Run: pip install pytesseract Pillow")
            ) from e
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {file_path}", error_code="E402", exc_info=True)
            raise TextExtractionError(
                file_path,
                cause=e,
            ) from e
    
    def extract_pages_from_file(self, file_path: str | Path) -> List[Tuple[int, str]]:
        """
        PDF 파일에서 페이지별 텍스트 추출
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            [(페이지번호, 텍스트), ...] 리스트
            
        Raises:
            PDFLoadError: PDF 로드 실패
            TextExtractionError: 텍스트 추출 실패
        """
        path = Path(file_path)
        
        if not path.exists():
            raise PDFLoadError(str(path), cause=FileNotFoundError(f"File not found: {path}"))
        
        if not path.suffix.lower() == ".pdf":
            raise PDFLoadError(str(path), cause=ValueError(f"Not a PDF file: {path}"))
        
        try:
            import pymupdf
            
            logger.info(f"PDF 처리 시작: {path.name}")
            
            doc = pymupdf.open(str(path))
            
            pages = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pages.append((page_num + 1, text))
            
            doc.close()
            
            logger.info(f"PDF 처리 완료: {len(pages)}페이지", count=len(pages))
            
            return pages
        
        except ImportError as e:
            logger.error(f"필수 라이브러리 누락: pymupdf", error_code="E402")
            raise TextExtractionError(
                str(path),
                cause=ImportError("pymupdf not installed. Run: pip install pymupdf")
            ) from e
        
        except Exception as e:
            logger.error(f"PDF 처리 실패: {path.name}", error_code="E402", exc_info=True)
            raise TextExtractionError(
                str(path),
                cause=e,
            ) from e

