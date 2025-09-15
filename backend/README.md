# AInBox Backend

Sistema de análise de e-mails com IA utilizando Google Gemini API. Classifica e-mails como produtivos/improdativos e gera sugestões de resposta em tempo real via WebSocket.

## 🚀 Tecnologias

- **FastAPI** - Framework web assíncrono
- **WebSockets** - Comunicação em tempo real
- **Google Gemini AI** - Análise e classificação de e-mails
- **NLTK** - Processamento de linguagem natural
- **Redis** - Rate limiting e cache
- **Docker** - Containerização
- **Google Cloud Run** - Deploy serverless

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

## ⚙️ Configuração

### Variáveis de Ambiente Obrigatórias

```bash
# Google Gemini API
GOOGLE_API_KEY=sua_chave_aqui

# Redis (Google Cloud Memorystore)
REDIS_HOST=10.53.247.67
REDIS_PASSWORD=sua_senha_redis
REDIS_SSL=true
```

### Setup Rápido

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis
cp env.example .env
# Editar .env com suas configurações

# 3. Executar localmente
python main.py
```

## 🚀 Deploy

### Google Cloud Run (Produção)

```bash
# Deploy automático via Cloud Build
git push origin main
# Trigger automático no Google Cloud Build
```

### Docker Local

```bash
# Build e execução
docker build -t ainbox-backend .
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your_api_key \
  -e REDIS_HOST=localhost \
  ainbox-backend
```

## 📡 API Endpoints

### Análise de E-mails

- `POST /api/v1/analysis/emails` - Análise de strings JSON
- `POST /api/v1/analysis/files` - Upload de arquivos (.pdf/.txt)

### WebSocket

- `WS /ws` - Resultados em tempo real

### Health Check

- `GET /api/v1/health/` - Status da aplicação
- `GET /api/v1/health/detailed` - Status detalhado

## 💬 WebSocket

### Tipos de Mensagem

- `analysis_result` - Resultado de análise de um e-mail
- `analysis_complete` - Análise concluída
- `error` - Mensagem de erro

### Exemplo JavaScript

```javascript
const ws = new WebSocket("wss://sua-api.com/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "analysis_result") {
    console.log("Email:", data.data.classification);
  }
};
```

## 📝 Exemplos de Uso

### Análise de Strings

```bash
curl -X POST "https://sua-api.com/api/v1/analysis/emails" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["Olá, preciso de uma reunião para discutir o projeto."],
    "context": "E-mails de trabalho",
    "connection_id": "conn_123"
  }'
```

### Upload de Arquivos

```bash
curl -X POST "https://sua-api.com/api/v1/analysis/files" \
  -F "files=@email.pdf" \
  -F "context=E-mails importantes" \
  -F "connection_id=conn_123"
```

### Resposta da Análise

```json
{
  "email_index": 1,
  "total_emails": 2,
  "classification": "Produtivo",
  "suggestion": "Sugestão de resposta gerada pela IA...",
  "nlp_analysis": {
    "language": "pt",
    "sentiment": "neutral",
    "key_phrases": ["reunião", "projeto"]
  }
}
```

## 🔒 Segurança

- **Rate Limiting**: 10 req/min por IP (Redis)
- **Validação de Arquivos**: Máx 20 arquivos, 5MB cada
- **CORS**: Configurado para frontend
- **WebSocket**: Validação de origem
- **Logs**: Estruturados para monitoramento

## ✨ Funcionalidades

- 🤖 **IA Google Gemini** - Classificação e sugestões
- 🔄 **WebSocket** - Resultados em tempo real
- 📄 **Upload de Arquivos** - PDF e TXT
- 🌐 **NLP Avançado** - Português brasileiro
- ⚡ **Rate Limiting** - Proteção contra spam
- 🐳 **Docker** - Containerização
- ☁️ **Google Cloud Run** - Deploy serverless
