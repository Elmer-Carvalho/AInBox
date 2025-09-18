# Estágio 1: Instalação das dependências
FROM node:18-alpine AS deps
WORKDIR /app

# Instala o pnpm
RUN npm install -g pnpm

# Copia os arquivos de manifesto e instala as dependências
COPY package.json pnpm-lock.yaml ./
    RUN pnpm install --no-frozen-lockfile

# Estágio 2: Build da aplicação
FROM node:18-alpine AS builder
WORKDIR /app
RUN npm install -g pnpm
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Seta a variável de ambiente para a URL do backend acessível do navegador
# Esta variável será sobrescrita pelo docker-compose em runtime
ENV NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

RUN pnpm build

# Estágio 3: Imagem final de produção
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Instala o pnpm no estágio final
RUN npm install -g pnpm

# Copia os artefatos de build
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["pnpm", "start"]
