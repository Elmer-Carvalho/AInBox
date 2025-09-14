"""
Email processing service
Handles email content extraction and processing with advanced NLP
"""

import re
from typing import Dict, Any, Optional
from loguru import logger

from app.services.ai_service import AIService
from app.services.nlp_processor import NLPProcessor


class EmailProcessor:
    """
    Service for processing email content
    """
    
    def __init__(self, ai_service: AIService):
        """
        Initialize email processor
        
        Args:
            ai_service: AI service instance for analysis
        """
        self.ai_service = ai_service
        self.nlp_processor = NLPProcessor()
        logger.info("Email processor initialized with advanced NLP capabilities")
    
    async def process_single_email(
        self,
        email_content: str,
        context: Optional[str] = None,
        email_index: int = 1,
        total_emails: int = 1
    ) -> Dict[str, Any]:
        """
        Process a single email through AI analysis
        
        Args:
            email_content: Raw email content
            context: Optional context for analysis
            email_index: Current email index (1-based)
            total_emails: Total number of emails being processed
            
        Returns:
            Dict[str, Any]: Processed email result
        """
        try:
            # Advanced NLP processing
            nlp_result = self.nlp_processor.process_text(email_content)
            
            # Use processed text for AI analysis
            processed_content = nlp_result.get('processed_text', email_content)
            
            # Analyze with AI using processed content and detected language
            detected_language = nlp_result.get('language', 'en')
            ai_result = await self.ai_service.analyze_email(processed_content, context, detected_language)
            
            # Build comprehensive result
            result = {
                "email_index": email_index,
                "total_emails": total_emails,
                "classification": ai_result.get("classificacao", "Error"),
                "suggestion": ai_result.get("sugestao_resposta"),
                "original_content": email_content[:200] + "..." if len(email_content) > 200 else email_content,
                "processed_content": processed_content[:200] + "..." if len(processed_content) > 200 else processed_content,
                "nlp_analysis": {
                    "language": nlp_result.get('language', 'unknown'),
                    "sentiment": nlp_result.get('sentiment', {}),
                    "word_count": nlp_result.get('word_count', 0),
                    "processing_metadata": nlp_result.get('processing_metadata', {})
                }
            }
            
            # Add error information if present
            if "error" in ai_result:
                result["error"] = ai_result["error"]
            
            logger.info(f"Email {email_index}/{total_emails} processed: {result['classification']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing email {email_index}: {e}")
            return {
                "email_index": email_index,
                "total_emails": total_emails,
                "classification": "Error",
                "suggestion": None,
                "error": str(e),
                "original_content": email_content[:200] + "..." if len(email_content) > 200 else email_content
            }
    
    def _clean_email_content(self, content: str) -> str:
        """
        Clean and normalize email content using advanced NLP processing
        
        Args:
            content: Raw email content
            
        Returns:
            str: Cleaned email content
        """
        if not content:
            return ""
        
        # Use NLP processor for advanced cleaning
        nlp_result = self.nlp_processor.process_text(content)
        return nlp_result.get('processed_text', content)
    
    def extract_email_metadata(self, content: str) -> Dict[str, str]:
        """
        Extract basic metadata from email content
        
        Args:
            content: Email content
            
        Returns:
            Dict[str, str]: Extracted metadata
        """
        metadata = {}
        
        # Extract subject
        subject_match = re.search(r'Subject:\s*(.+)', content, re.IGNORECASE)
        if subject_match:
            metadata['subject'] = subject_match.group(1).strip()
        
        # Extract sender
        from_match = re.search(r'From:\s*(.+)', content, re.IGNORECASE)
        if from_match:
            metadata['sender'] = from_match.group(1).strip()
        
        # Extract recipient
        to_match = re.search(r'To:\s*(.+)', content, re.IGNORECASE)
        if to_match:
            metadata['recipient'] = to_match.group(1).strip()
        
        # Extract date
        date_match = re.search(r'Date:\s*(.+)', content, re.IGNORECASE)
        if date_match:
            metadata['date'] = date_match.group(1).strip()
        
        return metadata
    
    def validate_email_content(self, content: str) -> Dict[str, Any]:
        """
        Validate email content before processing
        
        Args:
            content: Email content to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not content or not content.strip():
            validation["is_valid"] = False
            validation["errors"].append("Email content is empty")
            return validation
        
        if len(content) < 10:
            validation["warnings"].append("Email content is very short")
        
        if len(content) > 50000:  # 50KB limit
            validation["is_valid"] = False
            validation["errors"].append("Email content is too long (max 50KB)")
        
        # Check for suspicious content patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:text/html',  # Data URLs
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                validation["warnings"].append("Email contains potentially suspicious content")
                break
        
        return validation
