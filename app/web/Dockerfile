# Next.js image with separate dev and production targets.
# Use `target: dev` in docker-compose for hot-reload local dev.
# Use `target: runner` for Fly.io production.

FROM node:20-alpine AS base
WORKDIR /app
RUN corepack enable

# ---- dev target: bind-mount source, watch-mode ----
FROM base AS dev
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]

# ---- production build ----
FROM base AS builder
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# ---- production runner: standalone output ----
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
