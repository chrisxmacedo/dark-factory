# ---- base ----
FROM node:22-alpine AS base
WORKDIR /app

# ---- deps ----
FROM base AS deps
COPY package.json package-lock.json ./
COPY prisma ./prisma/
RUN npm ci --ignore-scripts && npx prisma generate

# ---- builder ----
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- runner ----
FROM base AS runner
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 orchestrator && \
    adduser --system --uid 1001 orchestrator

COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
COPY --from=builder /app/prisma ./prisma

USER orchestrator

EXPOSE 8080

CMD ["node", "dist/index.js"]
