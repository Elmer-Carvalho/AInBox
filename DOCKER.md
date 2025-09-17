# 🐳 AInBox - Ambiente Local com Docker

Este guia explica como executar o AInBox localmente usando Docker Compose.

## 📋 Pré-requisitos

- [Docker](https://www.docker.com/get-started) instalado
- [Docker Compose](https://docs.docker.com/compose/install/) instalado
- Chave da API do Google Gemini

## 🚀 Como Executar

### 1. Configure a Chave da API

Edite o arquivo `backend/.env` e substitua `SUA_CHAVE_API_DO_GEMINI_AQUI` pela sua chave real:

```bash
GOOGLE_API_KEY=sua_chave_real_aqui
```

### 2. Execute o Ambiente Completo

Na raiz do projeto, execute:

```bash
docker-compose up --build
```

**Primeira execução:** Use `--build` para construir as imagens
**Execuções seguintes:** Use apenas `docker-compose up`

### 3. Acesse as Aplicações

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Documentação da API:** http://localhost:8000/docs
- **Redis:** localhost:6379

## 🛠️ Comandos Úteis

### Parar os Serviços
```bash
docker-compose down
```

### Parar e Remover Volumes
```bash
docker-compose down -v
```

### Ver Logs
```bash
docker-compose logs -f
```

### Reconstruir um Serviço Específico
```bash
docker-compose up --build frontend
```

## 📁 Estrutura dos Serviços

### Backend (FastAPI)
- **Porta:** 8000
- **Arquivo de configuração:** `backend/.env`
- **Comando:** `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### Frontend (Next.js)
- **Porta:** 3000
- **Arquivo de configuração:** `frontend/.env.local`
- **Comando:** `pnpm start`

### Redis
- **Porta:** 6379
- **Imagem:** `redis:alpine`
- **Dados persistentes:** Volume `redis_data`

## 🔧 Configurações

### Variáveis de Ambiente do Frontend
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Variáveis de Ambiente do Backend
```bash
# Aplicação
APP_NAME=AInBox API - Local
ENVIRONMENT=development
DEBUG=true

# Servidor
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Redis Local
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_SSL=false
```

## 🐛 Troubleshooting

### Problema: Porta já em uso
```bash
# Verifique se alguma aplicação está usando as portas
netstat -an | findstr :3000
netstat -an | findstr :8000
netstat -an | findstr :6379
```

### Problema: Erro de permissão no Docker
```bash
# No Windows, execute como administrador
# No Linux/Mac, adicione seu usuário ao grupo docker
sudo usermod -aG docker $USER
```

### Problema: Cache do Docker
```bash
# Limpe o cache e reconstrua
docker-compose down
docker system prune -a
docker-compose up --build
```

## 📝 Notas Importantes

- O arquivo `.env` do backend contém a chave da API do Gemini - **nunca commite este arquivo**
- O arquivo `.env.local` do frontend é para desenvolvimento local
- Os volumes garantem que as mudanças no código sejam refletidas automaticamente
- O Redis mantém os dados entre reinicializações do Docker

## 🎯 Próximos Passos

1. Configure sua chave da API do Gemini
2. Execute `docker-compose up --build`
3. Acesse http://localhost:3000
4. Teste a funcionalidade completa do AInBox!
