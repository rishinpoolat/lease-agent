# Dev-style image: bind-mounts source, runs `next dev`. Not a hardened
# multi-stage production build -- see README "what I left out."
FROM node:22-slim

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
