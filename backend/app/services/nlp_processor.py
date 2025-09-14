"""
Advanced NLP processing service using NLTK, spaCy and other specialized libraries
"""

import re
import string
import unicodedata
from typing import Dict, List, Tuple, Optional, Any
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from textblob import TextBlob
from langdetect import detect, DetectorFactory
from loguru import logger

# Set seed for consistent language detection
DetectorFactory.seed = 0


class NLPProcessor:
    """
    Advanced NLP processing service for email content
    """
    
    def __init__(self):
        """Initialize NLP processor with required resources"""
        self._download_nltk_resources()
        self._initialize_components()
        logger.info("NLP Processor initialized with advanced preprocessing capabilities")
    
    def _download_nltk_resources(self) -> None:
        """Download required NLTK resources"""
        try:
            nltk_data = [
                'punkt',
                'stopwords', 
                'wordnet',
                'averaged_perceptron_tagger',
                'maxent_ne_chunker',
                'words'
            ]
            
            for resource in nltk_data:
                try:
                    # Check if resource exists with different paths
                    if resource in ['punkt', 'stopwords', 'wordnet', 'words']:
                        nltk.data.find(f'tokenizers/{resource}')
                    elif resource == 'averaged_perceptron_tagger':
                        nltk.data.find(f'taggers/{resource}')
                    elif resource == 'maxent_ne_chunker':
                        nltk.data.find(f'chunkers/{resource}')
                    else:
                        nltk.data.find(resource)
                except LookupError:
                    logger.info(f"Downloading NLTK resource: {resource}")
                    nltk.download(resource, quiet=True)
                    
        except Exception as e:
            logger.warning(f"Error downloading NLTK resources: {e}")
    
    def _initialize_components(self) -> None:
        """Initialize NLP components"""
        # Initialize stemmer
        self.stemmer = PorterStemmer()
        
        # Get stopwords for multiple languages
        self.stop_words = {
            'en': set(stopwords.words('english')),
            'pt': set(stopwords.words('portuguese')),
            'es': set(stopwords.words('spanish')),
            'fr': set(stopwords.words('french')),
            'de': set(stopwords.words('german'))
        }
        
        # Add Brazilian Portuguese specific stopwords
        self._add_brazilian_stopwords()
        
        # Common stopwords for email processing
        self.email_stopwords = {
            'email', 'mail', 'message', 'sent', 'received', 'forwarded',
            'reply', 're:', 'fwd:', 'subject:', 'from:', 'to:', 'cc:',
            'bcc:', 'date:', 'attached', 'attachment', 'please', 'thank',
            'thanks', 'regards', 'best', 'sincerely', 'dear', 'hi', 'hello',
            # Portuguese email stopwords
            'e-mail', 'mensagem', 'enviado', 'recebido', 'encaminhado',
            'resposta', 're:', 'fwd:', 'assunto:', 'de:', 'para:', 'cc:',
            'cópia:', 'data:', 'anexo', 'anexado', 'por favor', 'obrigado',
            'obrigada', 'atenciosamente', 'cordiais', 'saudações', 'olá'
        }
    
    def _add_brazilian_stopwords(self) -> None:
        """Add Brazilian Portuguese specific stopwords"""
        brazilian_stopwords = {
            # Common Brazilian Portuguese words
            'aí', 'aqui', 'ali', 'lá', 'aonde', 'onde', 'quando',
            'como', 'porque', 'porquê', 'por que', 'então', 'assim', 'também',
            'tambem', 'mesmo', 'mesma', 'mesmos', 'mesmas', 'outro', 'outra',
            'outros', 'outras', 'todo', 'toda', 'todos', 'todas', 'cada',
            'qualquer', 'algum', 'alguma', 'alguns', 'algumas', 'nenhum',
            'nenhuma', 'nenhuns', 'nenhumas', 'muito', 'muita', 'muitos',
            'muitas', 'pouco', 'pouca', 'poucos', 'poucas', 'mais', 'menos',
            'bem', 'mal', 'melhor', 'pior', 'grande', 'pequeno', 'novo',
            'velho', 'jovem', 'antigo', 'moderno', 'atual', 'passado',
            'futuro', 'presente', 'hoje', 'ontem', 'amanhã', 'agora',
            'depois', 'antes', 'durante', 'enquanto', 'sempre',
            'nunca', 'jamais', 'talvez', 'provavelmente', 'certamente',
            'obviamente', 'claramente', 'evidentemente', 'realmente',
            'verdadeiramente', 'efetivamente', 'praticamente', 'basicamente',
            'principalmente', 'especialmente', 'particularmente', 'especificamente',
            'geralmente', 'normalmente', 'habitualmente', 'frequentemente',
            'raramente', 'ocasionalmente', 'eventualmente', 'finalmente',
            'inicialmente', 'primeiramente', 'ultimamente', 'recentemente',
            'atualmente', 'presentemente', 'momentaneamente', 'temporariamente',
            'permanentemente', 'definitivamente', 'conclusivamente',
            'decisivamente', 'determinadamente', 'resolutamente', 'firmemente',
            'solidamente', 'estavelmente', 'constantemente', 'continuamente',
            'incessantemente', 'perpetuamente', 'eternamente', 'infinitamente',
            'indefinidamente', 'indeterminadamente', 'indecisamente', 'hesitantemente',
            'dubitativamente', 'incertamente', 'inseguramente', 'precariamente',
            'instavelmente', 'volatilmente', 'mudavelmente', 'variadamente',
            'diferentemente', 'distintamente', 'separadamente', 'individualmente',
            'coletivamente', 'grupadamente', 'juntamente', 'simultaneamente',
            'concomitantemente', 'paralelamente', 'consecutivamente', 'sequencialmente',
            'sucessivamente', 'progressivamente', 'gradualmente', 'lentamente',
            'rapidamente', 'velozmente', 'depressa', 'devagar', 'calmamente',
            'tranquilamente', 'pacificamente', 'serenamente', 'quietamente',
            'silenciosamente', 'secretamente', 'privadamente', 'pessoalmente',
            'individualmente', 'particularmente', 'especificamente', 'especialmente',
            'principalmente', 'sobretudo', 'detalhadamente', 'minuciosamente', 'cuidadosamente',
            'atentamente', 'observantemente', 'vigilantemente', 'cautelosamente',
            'prudentemente', 'sabiamente', 'inteligentemente', 'esperto',
            'esperta', 'inteligente', 'sábio', 'sábia'
        }
        
        # Add to Portuguese stopwords
        self.stop_words['pt'].update(brazilian_stopwords)
    
    def process_text(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Simplified text processing pipeline optimized for Gemini AI
        
        Args:
            text: Input text to process
            language: Detected or specified language
            
        Returns:
            Dict[str, Any]: Processed text and metadata
        """
        if not text or not text.strip():
            return self._empty_result()
        
        try:
            # Detect language if not provided
            if not language:
                language = self.detect_language(text)
            
            # Basic cleaning and normalization
            cleaned_text = self._clean_and_normalize(text)
            
            # Simple tokenization for basic analysis
            tokens = self._tokenize(cleaned_text, language)
            
            # Basic stopword removal
            filtered_tokens = self._remove_stopwords(tokens, language)
            
            # Reconstruct processed text (simplified)
            processed_text = ' '.join(filtered_tokens)
            
            # Basic sentiment analysis
            sentiment = self._analyze_sentiment(cleaned_text)
            
            return {
                'original_text': text,
                'processed_text': processed_text,
                'language': language,
                'tokens': filtered_tokens,
                'sentiment': sentiment,
                'word_count': len(filtered_tokens),
                'char_count': len(processed_text),
                'processing_metadata': {
                    'original_length': len(text),
                    'cleaned_length': len(cleaned_text),
                    'token_count': len(tokens),
                    'filtered_token_count': len(filtered_tokens)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in NLP processing: {e}")
            return self._error_result(str(e))
    
    def detect_language(self, text: str) -> str:
        """
        Detect text language
        
        Args:
            text: Input text
            
        Returns:
            str: Detected language code
        """
        try:
            # Use langdetect for language detection
            detected_lang = detect(text)
            
            # Map to supported languages
            lang_mapping = {
                'en': 'en', 'pt': 'pt', 'es': 'es', 
                'fr': 'fr', 'de': 'de'
            }
            
            return lang_mapping.get(detected_lang, 'en')
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def _clean_and_normalize(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Input text
            
        Returns:
            str: Cleaned text
        """
        # Remove email headers
        text = self._remove_email_headers(text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove accented characters (optional)
        # text = unidecode.unidecode(text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove phone numbers
        text = re.sub(r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text.strip()
    
    def _remove_email_headers(self, text: str) -> str:
        """
        Remove email headers and metadata
        
        Args:
            text: Input text
            
        Returns:
            str: Text without headers
        """
        lines = text.split('\n')
        content_lines = []
        skip_headers = True
        
        for line in lines:
            line = line.strip()
            
            if skip_headers:
                # Check if line looks like a header
                if (line.startswith(('From:', 'To:', 'Subject:', 'Date:', 'Cc:', 'Bcc:', 
                                   'Reply-To:', 'Message-ID:', 'X-', 'Return-Path:')) or
                    line == '' or
                    re.match(r'^[A-Za-z-]+:\s*', line)):
                    continue
                else:
                    skip_headers = False
                    if line:
                        content_lines.append(line)
            else:
                content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def _tokenize(self, text: str, language: str) -> List[str]:
        """
        Tokenize text into words
        
        Args:
            text: Input text
            language: Text language
            
        Returns:
            List[str]: List of tokens
        """
        try:
            # Use NLTK tokenizer
            tokens = word_tokenize(text.lower())
            
            # Filter out very short tokens and pure punctuation
            filtered_tokens = [
                token for token in tokens 
                if len(token) > 1 and not token in string.punctuation
            ]
            
            return filtered_tokens
            
        except Exception as e:
            logger.warning(f"Tokenization failed: {e}, using simple split")
            return text.lower().split()
    
    def _remove_stopwords(self, tokens: List[str], language: str) -> List[str]:
        """
        Remove stopwords from tokens
        
        Args:
            tokens: List of tokens
            language: Text language
            
        Returns:
            List[str]: Filtered tokens
        """
        # Get language-specific stopwords
        lang_stopwords = self.stop_words.get(language, self.stop_words['en'])
        
        # Combine with email-specific stopwords
        all_stopwords = lang_stopwords.union(self.email_stopwords)
        
        # Filter tokens
        filtered_tokens = [
            token for token in tokens 
            if token not in all_stopwords
        ]
        
        return filtered_tokens
    
    # Removed complex NLP methods to simplify for Gemini AI
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze text sentiment with Portuguese-specific improvements
        
        Args:
            text: Input text
            
        Returns:
            Dict[str, float]: Sentiment analysis results
        """
        try:
            # Basic TextBlob analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Portuguese-specific sentiment adjustments
            polarity = self._adjust_sentiment_for_portuguese(text, polarity)
            
            # Categorize sentiment
            if polarity > 0.1:
                sentiment_label = 'positive'
            elif polarity < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'label': sentiment_label
            }
            
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'label': 'neutral'
            }
    
    def _adjust_sentiment_for_portuguese(self, text: str, polarity: float) -> float:
        """
        Adjust sentiment analysis for Portuguese text
        
        Args:
            text: Input text
            polarity: Original polarity score
            
        Returns:
            float: Adjusted polarity score
        """
        # Portuguese positive words
        positive_words = [
            'obrigado', 'obrigada', 'obrigados', 'obrigadas', 'valeu', 'valeu',
            'perfeito', 'perfeita', 'excelente', 'ótimo', 'ótima', 'ótimos', 'ótimas',
            'bom', 'boa', 'bons', 'boas', 'legal', 'bacana', 'show', 'massa',
            'incrível', 'fantástico', 'fantástica', 'maravilhoso', 'maravilhosa',
            'incrível', 'sensacional', 'demais', 'top', 'show', 'massa',
            'sucesso', 'parabéns', 'congratulações', 'felicitações'
        ]
        
        # Portuguese negative words
        negative_words = [
            'problema', 'problemas', 'erro', 'erros', 'falha', 'falhas',
            'ruim', 'ruins', 'péssimo', 'péssima', 'péssimos', 'péssimas',
            'terrível', 'horrível', 'desastre', 'catástrofe', 'triste',
            'tristeza', 'depressão', 'angústia', 'sofrimento', 'dor',
            'raiva', 'ódio', 'frustração', 'decepção', 'desapontamento',
            'fracasso', 'falha', 'erro', 'mistake', 'bug', 'defeito'
        ]
        
        # Count positive and negative words
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Adjust polarity based on word counts
        if positive_count > negative_count:
            polarity += 0.2 * (positive_count - negative_count) / len(text.split())
        elif negative_count > positive_count:
            polarity -= 0.2 * (negative_count - positive_count) / len(text.split())
        
        # Clamp polarity to [-1, 1]
        return max(-1.0, min(1.0, polarity))
    
    # Removed key phrase extraction to simplify for Gemini AI
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result for empty input"""
        return {
            'original_text': '',
            'processed_text': '',
            'language': 'en',
            'tokens': [],
            'sentiment': {'polarity': 0.0, 'subjectivity': 0.0, 'label': 'neutral'},
            'word_count': 0,
            'char_count': 0,
            'processing_metadata': {
                'original_length': 0,
                'cleaned_length': 0,
                'token_count': 0,
                'filtered_token_count': 0
            }
        }
    
    def _error_result(self, error: str) -> Dict[str, Any]:
        """Return error result"""
        return {
            'original_text': '',
            'processed_text': '',
            'language': 'en',
            'tokens': [],
            'sentiment': {'polarity': 0.0, 'subjectivity': 0.0, 'label': 'neutral'},
            'word_count': 0,
            'char_count': 0,
            'error': error,
            'processing_metadata': {
                'original_length': 0,
                'cleaned_length': 0,
                'token_count': 0,
                'filtered_token_count': 0
            }
        }
