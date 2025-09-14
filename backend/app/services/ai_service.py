"""
AI Service for Google Gemini integration
"""

import json
from typing import Dict, Any, Optional
import google.generativeai as genai
from loguru import logger

from app.core.config import settings


class AIService:
    """
    Service for interacting with Google Gemini AI
    """
    
    def __init__(self):
        """Initialize AI service with Gemini configuration"""
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required")
        
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        logger.info(f"AI Service initialized with model: {settings.GEMINI_MODEL}")
    
    async def analyze_email(
        self, 
        email_content: str, 
        context: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Analyze email content using Gemini AI
        
        Args:
            email_content: The email content to analyze
            context: Optional context for better analysis
            language: Detected language of the email
            
        Returns:
            Dict[str, Any]: Analysis result with classification and suggestion
        """
        try:
            # Construct the prompt
            prompt = self._build_analysis_prompt(email_content, context, language)
            
            # Generate response from Gemini
            response = await self._generate_response(prompt)
            
            # Parse and validate response
            result = self._parse_ai_response(response)
            
            logger.debug(f"Email analyzed successfully: {result['classification']}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing email: {e}")
            return {
                "classification": "Error",
                "suggestion": None,
                "error": str(e)
            }
    
    def _build_analysis_prompt(self, email_content: str, context: Optional[str] = None, language: str = "en") -> str:
        """
        Build the analysis prompt for Gemini
        
        Args:
            email_content: Email content to analyze
            context: Optional context
            language: Detected language of the email
            
        Returns:
            str: Formatted prompt
        """
        # Language-specific instructions
        language_instructions = {
            "en": "Analyze the following email text. Classify it as \"Produtivo\" if it requires action or response, or \"Improdutivo\" if it doesn't.",
            "pt": "Analise o seguinte texto de e-mail. Classifique-o como \"Produtivo\" se exigir ação ou resposta, ou \"Improdutivo\" caso contrário.",
            "es": "Analiza el siguiente texto de correo electrónico. Clasifícalo como \"Produtivo\" si requiere acción o respuesta, o \"Improdutivo\" si no.",
            "fr": "Analysez le texte d'e-mail suivant. Classez-le comme \"Produtivo\" s'il nécessite une action ou une réponse, ou \"Improdutivo\" sinon.",
            "de": "Analysieren Sie den folgenden E-Mail-Text. Klassifizieren Sie ihn als \"Produtivo\", wenn eine Aktion oder Antwort erforderlich ist, oder \"Improdutivo\" wenn nicht."
        }
        
        base_instruction = language_instructions.get(language, language_instructions["en"])
        
        prompt = f"""{base_instruction}

Respond ONLY in JSON format, without any additional text or formatting. The JSON must contain two keys:
1. "classificacao": with the value "Produtivo" or "Improdutivo"
2. "sugestao_resposta": If the classification is "Produtivo", generate an appropriate textual response for the email in the same language as the email. If the classification is "Improdutivo", this key must be OBLIGATORILY null.

Email: "{email_content}""""

        if context:
            prompt += f"\nAdditional Context: "{context}""
        
        return prompt
    
    async def _generate_response(self, prompt: str) -> str:
        """
        Generate response from Gemini AI
        
        Args:
            prompt: The prompt to send to AI
            
        Returns:
            str: AI response
        """
        try:
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate AI response
        
        Args:
            response: Raw AI response
            
        Returns:
            Dict[str, Any]: Parsed and validated result
        """
        try:
            # Clean response (remove markdown formatting if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            result = json.loads(cleaned_response)
            
            # Validate required fields
            if "classificacao" not in result:
                raise ValueError("Missing 'classificacao' field in AI response")
            
            if "sugestao_resposta" not in result:
                raise ValueError("Missing 'sugestao_resposta' field in AI response")
            
            # Validate classification values
            if result["classificacao"] not in ["Produtivo", "Improdutivo"]:
                raise ValueError(f"Invalid classification: {result['classificacao']}")
            
            # Validate suggestion logic
            if result["classificacao"] == "Improdutivo" and result["sugestao_resposta"] is not None:
                logger.warning("AI generated suggestion for 'Improdutivo' email, setting to null")
                result["sugestao_resposta"] = None
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            raise ValueError(f"Invalid JSON response from AI: {e}")
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Test connection to Gemini AI service
        
        Returns:
            bool: True if connection is successful
        """
        try:
            test_prompt = "Respond with 'OK' if you can process this request."
            response = await self._generate_response(test_prompt)
            logger.info("AI service connection test successful")
            return True
        except Exception as e:
            logger.error(f"AI service connection test failed: {e}")
            return False
