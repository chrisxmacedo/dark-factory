# ---- base ----
FROM node:22-alpine AS base
WORKDIR /app

# ---- deps ----
FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# ---- builder ----
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- runner ----
FROM base AS runner
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 realtime && \
    adduser --system --uid 1001 realtime

COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./

USER realtime

EXPOSE 8080

CMD ["node", "dist/index.js"]
