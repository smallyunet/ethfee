############################################
# Build stage: Node 20 + manual native packages
############################################
FROM node:20-bookworm AS builder
WORKDIR /app

ARG NEXT_PUBLIC_API_URL

# ⚠️  Don’t set NODE_ENV here – we need devDependencies to build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_TELEMETRY_DISABLED=1

# install *all* deps (prod + dev)
COPY package*.json ./
RUN npm ci --ignore-scripts \
 && npm install --no-save --include=optional \
      lightningcss-linux-x64-gnu @tailwindcss/oxide-linux-x64-gnu

# project sources
COPY tsconfig.json ./
COPY . .
RUN npm run build

############################################
# Runtime stage (prod-only)
############################################
FROM node:20-bookworm-slim
WORKDIR /app

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NODE_ENV=production

# only the production bundle
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["npm", "start"]
