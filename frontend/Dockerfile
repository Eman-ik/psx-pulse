# Frontend container -- Stage 3 deployment prep. Standard Next.js standalone multi-
# stage build (see next.config.ts's output: "standalone"): the final image copies
# only the traced server bundle, not the full node_modules.
FROM node:24-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# npm install, not npm ci: package-lock.json was generated on Windows and only
# records Windows-target optional native deps (confirmed: a Linux npm ci here fails
# with "Missing: @emnapi/... from lock file" for exactly that reason) -- ci's strict
# 1:1 lockfile match doesn't tolerate a cross-platform gap like that, install does.
RUN npm install

FROM node:24-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Same value NEXT_PUBLIC_API_BASE_URL has in .env.local for local dev -- baked in at
# build time since NEXT_PUBLIC_* vars are inlined into the client bundle, not read at
# runtime. Override with --build-arg for a deploy where the backend isn't at this URL.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:24-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN useradd --create-home appuser
COPY --from=builder /app/public ./public
COPY --from=builder --chown=appuser:appuser /app/.next/standalone ./
COPY --from=builder --chown=appuser:appuser /app/.next/static ./.next/static
USER appuser

EXPOSE 3000
CMD ["node", "server.js"]
