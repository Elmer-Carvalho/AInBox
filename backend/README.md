# AInBox Backend

Sistema de análise de e-mails com IA utilizando Google Gemini API.

## Tecnologias

- **FastAPI**: Framework web assíncrono
- **WebSockets**: Comunicação em tempo real
- **Google Gemini AI**: Análise e classificação de e-mails
- **NLTK**: Processamento avançado de linguagem natural
- **spaCy**: Análise linguística avançada
- **TextBlob**: Análise de sentimento e processamento de texto
- **Uvicorn**: Servidor ASGI
- **Pydantic**: Validação de dados

## Estrutura do Projeto

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── health.py      # Health check endpoints
│   │   │   └── analysis.py    # Email analysis endpoints
│   │   └── routes.py          # API routes configuration
│   ├── core/
│   │   └── config.py          # Application configuration
│   ├── services/
│   │   ├── ai_service.py      # Google Gemini integration
│   │   ├── email_processor.py # Email processing logic
│   │   └── nlp_processor.py   # Advanced NLP processing
│   └── websocket/
│       └── manager.py         # WebSocket connection management
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
└── env.example               # Environment variables template
```

## Configuração

1. **Instalar dependências**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variáveis de ambiente**:

   ```bash
   cp env.example .env
   # Editar .env com suas configurações
   ```

3. **Configurar recursos do NLTK**:

   ```bash
   python setup_nltk.py
   ```

4. **Configurar chave da API do Google**:
   - Obtenha uma chave da API do Google Gemini
   - Adicione no arquivo `.env`:
     ```
     GOOGLE_API_KEY=sua_chave_aqui
     ```

## Execução

### Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar NLTK
python setup_nltk.py

# Executar aplicação
python main.py
```

### Docker

```bash
# Build da imagem
docker build -t ainbox-backend .

# Executar container
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your_api_key \
  -e REDIS_HOST=localhost \
  ainbox-backend
```

### Google Cloud Run

```bash
# Deploy direto do código fonte
gcloud run deploy ainbox-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_API_KEY=your_api_key"
```

## Endpoints

### Health Check

- `GET /api/v1/health/` - Status básico da aplicação
- `GET /api/v1/health/detailed` - Status detalhado
- `GET /api/v1/health/rate-limit/{client_ip}` - Status de rate limiting
- `POST /api/v1/health/rate-limit/{client_ip}/reset` - Reset rate limiting (admin)

### Análise de E-mails

- `POST /api/v1/analysis/emails` - Iniciar análise de e-mails (strings JSON)
- `POST /api/v1/analysis/files` - Iniciar análise de e-mails (upload de arquivos .pdf/.txt)

### WebSocket

- `WS /ws` - Conexão WebSocket para resultados em tempo real

## WebSocket Messages

### Tipos de Mensagem

1. **connection_established**: Confirmação de conexão
2. **analysis_result**: Resultado de análise de um e-mail
3. **analysis_complete**: Análise de todos os e-mails concluída
4. **error**: Mensagem de erro

### Exemplo de Uso

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "analysis_result":
      console.log("Email analisado:", data.data);
      break;
    case "analysis_complete":
      console.log("Análise concluída");
      break;
  }
};
```

## Exemplos de Uso

### 1. Análise de Strings JSON

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      "Olá, preciso de uma reunião para discutir o projeto.",
      "Obrigado pelo e-mail, vou responder em breve."
    ],
    "context": "E-mails de trabalho",
    "connection_id": "conn_123"
  }'
```

### 2. Upload de Arquivos

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/files" \
  -F "files=@email1.pdf" \
  -F "files=@email2.txt" \
  -F "context=E-mails importantes" \
  -F "connection_id=conn_123"
```

### 3. Resposta da Análise

```json
{
  "email_index": 1,
  "total_emails": 2,
  "classification": "Produtivo",
  "suggestion": "Sugestão de resposta gerada pela IA...",
  "original_content": "Olá, preciso de uma reunião...",
  "processed_content": "preciso reunião discutir projeto",
  "nlp_analysis": {
    "language": "pt",
    "sentiment": {
      "polarity": 0.1,
      "subjectivity": 0.5,
      "label": "neutral"
    },
    "entities": [],
    "key_phrases": ["reunião", "projeto"],
    "word_count": 8,
    "processing_metadata": {
      "original_length": 50,
      "cleaned_length": 35,
      "token_count": 10,
      "filtered_token_count": 8
    }
  }
}
```

## Segurança

### Rate Limiting

- **10 requisições por minuto** por IP
- **Redis** para armazenamento distribuído
- **Fallback** para armazenamento em memória
- **Headers** de rate limiting nas respostas

### Validação de Arquivos

- **Máximo 20 arquivos** por requisição
- **Máximo 20 strings** por requisição
- **5MB por arquivo** (total 100MB)
- **Validação de tipo MIME**
- **Detecção de conteúdo suspeito**

### Monitoramento

- **Logs de segurança** estruturados
- **Métricas de rate limiting**
- **Status de validação** em tempo real
- **Reset de rate limiting** (admin)

## Funcionalidades

- ✅ Conexões WebSocket seguras e eficientes
- ✅ Análise de e-mails com Google Gemini AI
- ✅ Classificação binária (Produtivo/Improdutivo)
- ✅ Geração condicional de sugestões de resposta
- ✅ Processamento assíncrono em background
- ✅ **Processamento NLP simplificado e otimizado para Gemini**
- ✅ **Detecção automática de idioma**
- ✅ **Análise de sentimento para português brasileiro**
- ✅ **Normalização e limpeza inteligente de texto**
- ✅ **Remoção de stopwords para PT-BR**
- ✅ **Prompts multilíngues para IA**
- ✅ **Upload de arquivos .pdf e .txt**
- ✅ **Extração de texto de PDFs**
- ✅ **Processamento em memória (stateless)**
- ✅ **Rate limiting profissional com fastapi-limiter**
- ✅ **Validação de segurança de arquivos**
- ✅ **Limites de tamanho e quantidade**
- ✅ **Detecção de conteúdo suspeito**
- ✅ **Fallback para Redis indisponível**
- ✅ Health checks e monitoramento
- ✅ CORS configurado para frontend
- ✅ Logging estruturado
- ✅ Validação de dados com Pydantic
