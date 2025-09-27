# --- web-client (Next.js) ---
FROM node:20-alpine AS base
WORKDIR /app

# Copy only package metadata first for better layer caching
COPY package*.json ./
RUN npm ci --omit=dev

# Copy source and build
COPY . .
RUN npm run build

# Production image
FROM node:20-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY --from=base /app ./
EXPOSE 3000
CMD ["npm", "start"]
