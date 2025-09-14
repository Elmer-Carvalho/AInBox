# Deploy no Google Cloud Run

## 🚀 Deploy Simples

### Opção 1: Interface Web (Mais Fácil)

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Vá para **Cloud Run**
3. Clique em **"Criar Serviço"**
4. Selecione **"Deploy from source"**
5. Conecte seu repositório GitHub
6. Aponte para o **`Dockerfile`** na pasta `backend/`
7. Configure as variáveis de ambiente:
   - `GOOGLE_API_KEY`: Sua chave da API do Gemini
   - `REDIS_HOST`: IP do Redis (ou deixe vazio para desenvolvimento)
8. Clique em **"Deploy"**

### Opção 2: Google Cloud CLI

```bash
# Deploy direto do código fonte
gcloud run deploy ainbox-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_API_KEY=your_api_key"
```

### Opção 3: Docker + Cloud Run

```bash
# Build da imagem
docker build -t gcr.io/PROJECT_ID/ainbox-backend .

# Push para Registry
docker push gcr.io/PROJECT_ID/ainbox-backend

# Deploy
gcloud run deploy ainbox-backend \
  --image gcr.io/PROJECT_ID/ainbox-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔧 Variáveis de Ambiente

| Variável          | Descrição              | Obrigatória |
| ----------------- | ---------------------- | ----------- |
| `GOOGLE_API_KEY`  | Chave da API do Gemini | ✅ Sim      |
| `REDIS_HOST`      | IP do Redis (opcional) | ❌ Não      |
| `ALLOWED_ORIGINS` | Domínios permitidos    | ❌ Não      |

## 📊 Após o Deploy

- **Health Check**: `https://your-service-url/api/v1/health/`
- **API Docs**: `https://your-service-url/docs`
- **WebSocket**: `wss://your-service-url/ws`
