"""
File processing service for PDF and TXT files
Handles file upload, validation, and text extraction
"""

import io
from typing import Dict, Any, List, Optional
from fastapi import UploadFile, HTTPException
import PyPDF2
from loguru import logger

from app.core.config import settings


class FileProcessor:
    """
    Service for processing uploaded files and extracting text content
    """
    
    def __init__(self):
        """Initialize file processor"""
        self.allowed_extensions = settings.allowed_file_types_list
        self.max_file_size = settings.MAX_FILE_SIZE
        logger.info("File processor initialized")
    
    async def process_uploaded_files(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """
        Process multiple uploaded files and extract text content
        
        Args:
            files: List of uploaded files
            
        Returns:
            List[Dict[str, Any]]: List of processed files with extracted text
        """
        processed_files = []
        
        for file in files:
            try:
                # Validate file
                self._validate_file(file)
                
                # Extract text content
                text_content = await self._extract_text_from_file(file)
                
                # Create result
                result = {
                    'filename': file.filename,
                    'content_type': file.content_type,
                    'size': file.size,
                    'text_content': text_content,
                    'success': True
                }
                
                processed_files.append(result)
                logger.info(f"File processed successfully: {file.filename}")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                processed_files.append({
                    'filename': file.filename,
                    'content_type': file.content_type,
                    'size': file.size,
                    'text_content': '',
                    'success': False,
                    'error': str(e)
                })
        
        return processed_files
    
    def _validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file to validate
            
        Raises:
            HTTPException: If file validation fails
        """
        # Check if file has a name
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")
        
        # Check file extension
        file_extension = self._get_file_extension(file.filename)
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not allowed. Allowed types: {self.allowed_extensions}"
            )
        
        # Check file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size {file.size} exceeds maximum allowed size {self.max_file_size}"
            )
    
    def _get_file_extension(self, filename: str) -> str:
        """
        Get file extension from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            str: File extension (e.g., '.pdf', '.txt')
        """
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ''
    
    async def _extract_text_from_file(self, file: UploadFile) -> str:
        """
        Extract text content from uploaded file
        
        Args:
            file: Uploaded file
            
        Returns:
            str: Extracted text content
        """
        # Read file content into memory
        content = await file.read()
        
        # Reset file pointer for potential re-reading
        await file.seek(0)
        
        # Get file extension
        file_extension = self._get_file_extension(file.filename)
        
        # Extract text based on file type
        if file_extension == '.pdf':
            return self._extract_text_from_pdf(content)
        elif file_extension == '.txt':
            return self._extract_text_from_txt(content)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}"
            )
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF content
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            str: Extracted text
        """
        try:
            # Create PDF reader from bytes
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            
            # Extract text from all pages
            text_content = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
            
            # Clean up text
            text_content = text_content.strip()
            
            if not text_content:
                raise HTTPException(
                    status_code=400,
                    detail="No text content found in PDF file"
                )
            
            logger.info(f"PDF text extracted successfully, {len(text_content)} characters")
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Error extracting text from PDF: {str(e)}"
            )
    
    def _extract_text_from_txt(self, txt_content: bytes) -> str:
        """
        Extract text from TXT content
        
        Args:
            txt_content: TXT file content as bytes
            
        Returns:
            str: Extracted text
        """
        try:
            # Decode bytes to string
            text_content = txt_content.decode('utf-8')
            
            # Clean up text
            text_content = text_content.strip()
            
            if not text_content:
                raise HTTPException(
                    status_code=400,
                    detail="TXT file is empty"
                )
            
            logger.info(f"TXT text extracted successfully, {len(text_content)} characters")
            return text_content
            
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    text_content = txt_content.decode(encoding)
                    logger.info(f"TXT decoded with {encoding} encoding")
                    return text_content.strip()
                except UnicodeDecodeError:
                    continue
            
            raise HTTPException(
                status_code=400,
                detail="Unable to decode TXT file with supported encodings"
            )
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Error extracting text from TXT: {str(e)}"
            )
    
    def get_file_info(self, file: UploadFile) -> Dict[str, Any]:
        """
        Get information about uploaded file
        
        Args:
            file: Uploaded file
            
        Returns:
            Dict[str, Any]: File information
        """
        return {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': file.size,
            'extension': self._get_file_extension(file.filename) if file.filename else None
        }
