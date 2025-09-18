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
        language: str = "pt"
    ) -> Dict[str, Any]:
        """
        Analyze email content using Gemini AI with enhanced error handling.
        
        Args:
            email_content: The email content to analyze
            context: Optional context for better analysis
            language: Detected language of the email
            
        Returns:
            Dict[str, Any]: Analysis result with classification and suggestion
        """
        try:
            # Etapa 1: Construir o prompt
            prompt = self._build_analysis_prompt(email_content, context, language)
            
            raw_response_text = ""
            try:
                # Etapa 2: Gerar resposta do Gemini
                response = self.model.generate_content(prompt)
                
                # Log detalhado para depuração
                logger.debug(f"Raw Gemini response object: {response}")
                
                # Acessa o texto da resposta. Se a resposta foi bloqueada, isso pode gerar um erro.
                raw_response_text = response.text
                
            except Exception as gemini_error:
                # Captura o erro específico da biblioteca do Google
                logger.error(f"Error directly from Google API call ({type(gemini_error).__name__}): {gemini_error}")
                
                # Verifica se há informações de feedback no objeto de resposta
                if hasattr(gemini_error, '__dict__'):
                    logger.error(f"Gemini error details: {gemini_error.__dict__}")
                    
                # Propaga o erro para ser tratado pelo bloco externo
                raise gemini_error

            # Log do texto bruto antes de analisar
            logger.debug(f"Raw response text from Gemini: {raw_response_text}")
            
            # Etapa 3: Analisar a resposta
            result = self._parse_ai_response(raw_response_text)
            
            logger.debug(f"Email analyzed successfully: {result.get('classificacao')}")
            return result
            
        except Exception as e:
            # O bloco de captura geral agora fornecerá um erro muito mais informativo
            error_message = f"AI service failed during '{type(e).__name__}': {str(e)}"
            logger.error(f"Error analyzing email: {error_message}")
            return {
                "classification": "Error",
                "suggestion": None,
                "error": error_message
            }
    
    def _build_analysis_prompt(self, email_content: str, context: Optional[str] = None, language: str = "pt") -> str:
        """
        Build the analysis prompt for Gemini
        
        Args:
            email_content: Email content to analyze
            context: Optional context
            language: Detected language of the email
            
        Returns:
            str: Formatted prompt
        """
        # Language-specific instructions with improved prompt
        language_instructions = {
            "pt": """Analise os e-mails enviados e os classifique de duas formas:

- Produtivo: para e-mails pertinentes, como questões que envolvam trabalho, agendamento, reuniões ou qualquer outro aspecto que não deve ser deixado de lado e exija uma resposta.

- Improdutivo: felicitações de modo geral, spams ou qualquer outro assunto que não pareça exigir algum tipo de retorno.

Para os e-mails produtivos, você deve gerar uma resposta adequada, se baseando na sua interpretação e em qualquer contexto adicional passado. A resposta deve seguir bons padrões de organização e coesão, além de se assemelhar a e-mails em sua estrutura. Os improdutivos não exigem resposta, portanto, você deve ignorar.""",
            
            "en": """Analyze the emails sent and classify them in two ways:

- Produtivo: for relevant emails, such as work-related issues, scheduling, meetings or any other aspect that should not be overlooked and requires a response.

- Improdutivo: general congratulations, spam or any other subject that does not seem to require some kind of return.

For productive emails, you should generate an appropriate response, based on your interpretation and any additional context provided. The response should follow good organization and cohesion standards, and resemble emails in its structure. The unproductive ones do not require a response, so you should ignore them.""",
            
            "es": """Analiza los correos electrónicos enviados y clasifícalos de dos formas:

- Produtivo: para correos electrónicos pertinentes, como cuestiones que involucren trabajo, programación, reuniones o cualquier otro aspecto que no debe ser dejado de lado y exija una respuesta.

- Improdutivo: felicitaciones de modo general, spam o cualquier otro asunto que no parezca exigir algún tipo de retorno.

Para los correos electrónicos productivos, debes generar una respuesta adecuada, basándote en tu interpretación y en cualquier contexto adicional proporcionado. La respuesta debe seguir buenos estándares de organización y cohesión, además de asemejarse a correos electrónicos en su estructura. Los improductivos no exigen respuesta, por lo tanto, debes ignorarlos.""",
            
            "fr": """Analysez les e-mails envoyés et classez-les de deux façons:

- Produtivo: pour les e-mails pertinents, comme les questions qui impliquent le travail, la planification, les réunions ou tout autre aspect qui ne doit pas être laissé de côté et exige une réponse.

- Improdutivo: félicitations en général, spam ou tout autre sujet qui ne semble pas exiger un type de retour.

Pour les e-mails productifs, vous devez générer une réponse appropriée, en vous basant sur votre interprétation et sur tout contexte supplémentaire fourni. La réponse doit suivre de bons standards d'organisation et de cohésion, en plus de ressembler aux e-mails dans sa structure. Les improductifs n'exigent pas de réponse, donc vous devez les ignorer.""",
            
            "de": """Analysieren Sie die gesendeten E-Mails und klassifizieren Sie sie auf zwei Arten:

- Produtivo: für relevante E-Mails, wie arbeitsbezogene Fragen, Terminplanung, Meetings oder jeden anderen Aspekt, der nicht übersehen werden sollte und eine Antwort erfordert.

- Improdutivo: allgemeine Glückwünsche, Spam oder jedes andere Thema, das nicht zu erfordern scheint, eine Art von Rückgabe.

Für produktive E-Mails sollten Sie eine angemessene Antwort generieren, basierend auf Ihrer Interpretation und jedem zusätzlichen bereitgestellten Kontext. Die Antwort sollte guten Organisations- und Kohäsionsstandards folgen und E-Mails in ihrer Struktur ähneln. Die unproduktiven erfordern keine Antwort, daher sollten Sie sie ignorieren."""
        }
        
        base_instruction = language_instructions.get(language, language_instructions["pt"])
        
        prompt = f"""{base_instruction}

Respond ONLY in JSON format, without any additional text or formatting. The JSON must contain two keys:
1. "classificacao": with the value "Produtivo" or "Improdutivo" (keep these terms in Portuguese)
2. "sugestao_resposta": If the classification is "Produtivo", generate an appropriate textual response for the email in the same language as the email. If the classification is "Improdutivo", this key must be OBLIGATORILY null.

Email: "{email_content}"
"""

        if context:
            prompt += f"\nAdditional Context: \"{context}\""
        
        return prompt
    
    def _generate_response(self, prompt: str) -> str:
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
            response = self._generate_response(test_prompt)
            logger.info("AI service connection test successful")
            return True
        except Exception as e:
            logger.error(f"AI service connection test failed: {e}")
            return False