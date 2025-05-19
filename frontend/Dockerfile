############################################
# Build stage: Node 20 + manual native packages
############################################
FROM node:20-bookworm AS builder
WORKDIR /app

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY package*.json ./

RUN npm ci --ignore-scripts \
 && npm install --no-save --include=optional \
      lightningcss-linux-x64-gnu @tailwindcss/oxide-linux-x64-gnu

COPY . .
RUN npm run build

############################################
# Runtime stage (still Node 20)
############################################
FROM node:20-bookworm-slim
WORKDIR /app

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NODE_ENV=production

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["npm", "start"]
