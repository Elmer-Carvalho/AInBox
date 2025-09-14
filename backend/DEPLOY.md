# Deploy no Google Cloud Run

## 🚀 Deploy Automático (Recomendado)

### Opção 1: Cloud Build (CI/CD) - Configuração Automática

```bash
# Deploy via Cloud Build com todas as variáveis de ambiente configuradas automaticamente
gcloud builds submit --config cloudbuild.yaml
```

**Vantagens:**
- ✅ Configura automaticamente todas as variáveis de ambiente
- ✅ Faz build da imagem Docker
- ✅ Faz push para Artifact Registry
- ✅ Deploy no Cloud Run com configurações otimizadas
- ⚠️ **Lembre-se de configurar as variáveis sensíveis manualmente**

### Opção 2: Interface Web (Mais Fácil)

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Vá para **Cloud Run**
3. Clique em **"Criar Serviço"**
4. Selecione **"Deploy from source"**
5. Conecte seu repositório GitHub
6. Aponte para o **`Dockerfile`** na pasta `backend/`
7. **As variáveis de ambiente são configuradas automaticamente!**
8. Configure apenas as variáveis sensíveis:
   - `GOOGLE_API_KEY`: Sua chave da API do Gemini
   - `REDIS_PASSWORD`: Senha do Redis (se aplicável)
   - `REDIS_HOST`: IP do Redis em produção (se diferente de localhost)
9. Clique em **"Deploy"**

### Opção 3: Google Cloud CLI (Manual)

```bash
# Deploy direto do código fonte
gcloud run deploy ainbox-backend \
  --source . \
  --platform managed \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_API_KEY=your_api_key"
```

## 🔧 Variáveis de Ambiente

### ✅ **Configuradas Automaticamente**
| Variável | Valor Padrão | Descrição |
|----------|--------------|-----------|
| `APP_NAME` | AInBox API | Nome da aplicação |
| `VERSION` | 1.0.0 | Versão da aplicação |
| `ENVIRONMENT` | production | Ambiente de execução |
| `DEBUG` | false | Modo debug |
| `HOST` | 0.0.0.0 | Host de bind |
| `ALLOWED_ORIGINS` | * | Origens permitidas para CORS |
| `GEMINI_MODEL` | gemini-1.5-flash | Modelo do Gemini |
| `WS_HEARTBEAT_INTERVAL` | 30 | Intervalo de heartbeat WebSocket |
| `WS_MAX_CONNECTIONS` | 100 | Máximo de conexões WebSocket |
| `MAX_FILE_SIZE` | 5242880 | Tamanho máximo de arquivo (5MB) |
| `MAX_TOTAL_SIZE` | 104857600 | Tamanho total máximo (100MB) |
| `MAX_FILES_PER_REQUEST` | 20 | Máximo de arquivos por requisição |
| `MAX_STRINGS_PER_REQUEST` | 20 | Máximo de strings por requisição |
| `ALLOWED_FILE_TYPES` | .txt,.pdf | Tipos de arquivo permitidos |
| `RATE_LIMIT_PER_MINUTE` | 10 | Rate limit por minuto |
| `RATE_LIMIT_WINDOW` | 60 | Janela de rate limit (segundos) |
| `RATE_LIMIT_BURST` | 5 | Burst de rate limit |
| `REDIS_HOST` | localhost | Host do Redis |
| `REDIS_PORT` | 6379 | Porta do Redis |
| `REDIS_DB` | 0 | Database do Redis |
| `REDIS_SSL` | false | SSL do Redis |
| `REDIS_TTL` | 60 | TTL do Redis (segundos) |
| `LOG_LEVEL` | info | Nível de log |

### ⚠️ **Configuração Manual Obrigatória**
| Variável | Descrição | Como Configurar |
|----------|-----------|-----------------|
| `GOOGLE_API_KEY` | Chave da API do Gemini | `gcloud run services update ainbox-backend --region=southamerica-east1 --set-env-vars='GOOGLE_API_KEY=sua_chave'` |
| `REDIS_PASSWORD` | Senha do Redis (se aplicável) | `gcloud run services update ainbox-backend --region=southamerica-east1 --set-env-vars='REDIS_PASSWORD=senha'` |
| `REDIS_HOST` | IP do Redis em produção | `gcloud run services update ainbox-backend --region=southamerica-east1 --set-env-vars='REDIS_HOST=ip_redis'` |

## 📊 Após o Deploy

- **Health Check**: `https://your-service-url/api/v1/health/`
- **API Docs**: `https://your-service-url/docs`
- **WebSocket**: `wss://your-service-url/ws`
