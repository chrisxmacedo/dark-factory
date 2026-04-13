# --- Build stage ---
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json ./
COPY prisma ./prisma/
RUN npx prisma generate

COPY src ./src/
RUN npm run build

# --- Production stage ---
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/dist ./dist/
COPY prisma ./prisma/

# No EXPOSE — batch jobs do not serve HTTP
# No HEALTHCHECK — batch jobs run and exit

# Default: run the job specified by JOB_NAME env var
CMD ["node", "dist/index.js"]
