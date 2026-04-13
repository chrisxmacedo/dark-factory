FROM node:20-slim AS base
WORKDIR /app

# --- Build stage ---
FROM base AS build

COPY package.json package-lock.json* ./
RUN npm ci

COPY tsconfig.json ./
COPY src/ ./src/

RUN npm run build

# --- Production stage ---
FROM base AS production

ENV NODE_ENV=production

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=build /app/dist/ ./dist/

EXPOSE 3000

USER node

CMD ["node", "dist/server.js"]
