"""
Security validation service
Handles file size, quantity, and content validation
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from loguru import logger

from app.core.config import settings


class SecurityValidator:
    """
    Service for validating file uploads and request security
    """
    
    def __init__(self):
        """Initialize security validator"""
        self.max_file_size = settings.MAX_FILE_SIZE
        self.max_total_size = settings.MAX_TOTAL_SIZE
        self.max_files_per_request = settings.MAX_FILES_PER_REQUEST
        self.max_strings_per_request = settings.MAX_STRINGS_PER_REQUEST
        self.allowed_file_types = settings.ALLOWED_FILE_TYPES
        
        logger.info("Security validator initialized")
    
    def validate_file_upload_request(
        self, 
        files: List[UploadFile], 
        strings: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate file upload request for security
        
        Args:
            files: List of uploaded files
            strings: List of string contents
            
        Returns:
            Dict[str, Any]: Validation result
            
        Raises:
            HTTPException: If validation fails
        """
        validation_result = {
            "valid": True,
            "total_files": len(files),
            "total_strings": len(strings) if strings else 0,
            "total_size": 0,
            "warnings": [],
            "errors": []
        }
        
        try:
            # Validate file count
            if len(files) > self.max_files_per_request:
                raise HTTPException(
                    status_code=400,
                    detail=f"Too many files. Maximum allowed: {self.max_files_per_request}, received: {len(files)}"
                )
            
            # Validate string count
            if strings and len(strings) > self.max_strings_per_request:
                raise HTTPException(
                    status_code=400,
                    detail=f"Too many string contents. Maximum allowed: {self.max_strings_per_request}, received: {len(strings)}"
                )
            
            # Validate total content count
            total_content = len(files) + (len(strings) if strings else 0)
            if total_content > (self.max_files_per_request + self.max_strings_per_request):
                raise HTTPException(
                    status_code=400,
                    detail=f"Too many total contents. Maximum allowed: {self.max_files_per_request + self.max_strings_per_request}, received: {total_content}"
                )
            
            # Validate each file
            total_size = 0
            for file in files:
                file_validation = self._validate_single_file(file)
                validation_result["warnings"].extend(file_validation.get("warnings", []))
                
                if not file_validation["valid"]:
                    validation_result["errors"].extend(file_validation.get("errors", []))
                    raise HTTPException(
                        status_code=400,
                        detail=f"File validation failed: {', '.join(file_validation.get('errors', []))}"
                    )
                
                total_size += file_validation["size"]
            
            # Validate total size
            if total_size > self.max_total_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Total file size exceeds limit. Maximum allowed: {self.max_total_size / (1024*1024):.1f}MB, received: {total_size / (1024*1024):.1f}MB"
                )
            
            # Validate string contents
            if strings:
                for i, string_content in enumerate(strings):
                    string_validation = self._validate_string_content(string_content, i)
                    validation_result["warnings"].extend(string_validation.get("warnings", []))
                    
                    if not string_validation["valid"]:
                        validation_result["errors"].extend(string_validation.get("errors", []))
                        raise HTTPException(
                            status_code=400,
                            detail=f"String content validation failed: {', '.join(string_validation.get('errors', []))}"
                        )
            
            validation_result["total_size"] = total_size
            validation_result["valid"] = True
            
            logger.info(f"File upload validation passed: {len(files)} files, {len(strings) if strings else 0} strings, {total_size / (1024*1024):.1f}MB")
            
            return validation_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File upload validation error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"File validation error: {str(e)}"
            )
    
    def _validate_single_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate a single uploaded file
        
        Args:
            file: Uploaded file
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation = {
            "valid": True,
            "size": 0,
            "warnings": [],
            "errors": []
        }
        
        try:
            # Check if file has a name
            if not file.filename:
                validation["errors"].append("File must have a filename")
                validation["valid"] = False
                return validation
            
            # Check file extension
            file_extension = self._get_file_extension(file.filename)
            if file_extension not in self.allowed_file_types:
                validation["errors"].append(f"File type {file_extension} not allowed. Allowed types: {self.allowed_file_types}")
                validation["valid"] = False
                return validation
            
            # Check file size
            if file.size and file.size > self.max_file_size:
                validation["errors"].append(f"File size {file.size / (1024*1024):.1f}MB exceeds maximum allowed {self.max_file_size / (1024*1024):.1f}MB")
                validation["valid"] = False
                return validation
            
            # Validate MIME type (basic check)
            if file.content_type:
                expected_mime_types = {
                    '.pdf': 'application/pdf',
                    '.txt': 'text/plain'
                }
                
                expected_mime = expected_mime_types.get(file_extension)
                if expected_mime and not file.content_type.startswith(expected_mime.split('/')[0]):
                    validation["warnings"].append(f"File MIME type {file.content_type} doesn't match extension {file_extension}")
            
            # Check for suspicious filename patterns
            if self._is_suspicious_filename(file.filename):
                validation["warnings"].append("Filename contains suspicious patterns")
            
            validation["size"] = file.size or 0
            
            return validation
            
        except Exception as e:
            validation["errors"].append(f"File validation error: {str(e)}")
            validation["valid"] = False
            return validation
    
    def _validate_string_content(self, content: str, index: int) -> Dict[str, Any]:
        """
        Validate string content
        
        Args:
            content: String content
            index: Content index
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        try:
            # Check if content is empty
            if not content or not content.strip():
                validation["errors"].append(f"String content {index} is empty")
                validation["valid"] = False
                return validation
            
            # Check content length
            if len(content) > 100000:  # 100KB limit for strings
                validation["errors"].append(f"String content {index} is too long (max 100KB)")
                validation["valid"] = False
                return validation
            
            # Check for suspicious content patterns
            if self._is_suspicious_content(content):
                validation["warnings"].append(f"String content {index} contains suspicious patterns")
            
            # Check for excessive repetition (potential spam)
            if self._has_excessive_repetition(content):
                validation["warnings"].append(f"String content {index} has excessive repetition")
            
            return validation
            
        except Exception as e:
            validation["errors"].append(f"String content validation error: {str(e)}")
            validation["valid"] = False
            return validation
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ''
    
    def _is_suspicious_filename(self, filename: str) -> bool:
        """Check if filename contains suspicious patterns"""
        suspicious_patterns = [
            '..',  # Path traversal
            '/',   # Path separator
            '\\',  # Windows path separator
            '<',   # HTML/XML tags
            '>',   # HTML/XML tags
            '|',   # Command separator
            '&',   # Command separator
            ';',   # Command separator
            '`',   # Command substitution
            '$',   # Variable substitution
            '(',   # Command grouping
            ')',   # Command grouping
        ]
        
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in suspicious_patterns)
    
    def _is_suspicious_content(self, content: str) -> bool:
        """Check if content contains suspicious patterns"""
        suspicious_patterns = [
            '<script',  # Script tags
            'javascript:',  # JavaScript URLs
            'data:text/html',  # Data URLs
            'vbscript:',  # VBScript
            'onload=',  # Event handlers
            'onerror=',  # Event handlers
            'eval(',  # JavaScript eval
            'document.cookie',  # Cookie access
            'document.write',  # Document writing
        ]
        
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in suspicious_patterns)
    
    def _has_excessive_repetition(self, content: str) -> bool:
        """Check if content has excessive repetition (potential spam)"""
        # Split into words
        words = content.split()
        
        if len(words) < 10:
            return False
        
        # Count word frequency
        word_count = {}
        for word in words:
            word_lower = word.lower()
            word_count[word_lower] = word_count.get(word_lower, 0) + 1
        
        # Check if any word appears more than 30% of the time
        max_frequency = max(word_count.values())
        return max_frequency > len(words) * 0.3
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "max_total_size_mb": self.max_total_size / (1024 * 1024),
            "max_files_per_request": self.max_files_per_request,
            "max_strings_per_request": self.max_strings_per_request,
            "allowed_file_types": self.allowed_file_types
        }


# Global security validator instance
security_validator = SecurityValidator()
