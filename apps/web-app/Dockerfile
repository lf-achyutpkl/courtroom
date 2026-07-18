FROM node:22-bookworm-slim AS deps

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN corepack enable

WORKDIR /app/apps/web-app

COPY apps/web-app/package.json ./
COPY apps/web-app/pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

FROM node:22-bookworm-slim AS builder

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN corepack enable

WORKDIR /app/apps/web-app

COPY --from=deps /app/apps/web-app/node_modules ./node_modules
COPY apps/web-app ./

RUN pnpm build

FROM node:22-bookworm-slim AS runner

ENV NODE_ENV=production
ENV PORT=3000
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN corepack enable

WORKDIR /app/apps/web-app

COPY --from=builder /app/apps/web-app/package.json ./package.json
COPY --from=builder /app/apps/web-app/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=builder /app/apps/web-app/node_modules ./node_modules
COPY --from=builder /app/apps/web-app/.next ./.next
COPY --from=builder /app/apps/web-app/public ./public
COPY --from=builder /app/apps/web-app/app ./app

EXPOSE 3000

CMD ["pnpm", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
