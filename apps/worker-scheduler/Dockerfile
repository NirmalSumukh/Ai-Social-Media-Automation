# apps/worker-scheduler/Dockerfile
FROM node:20-alpine

# 1. build stage
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev          # install prod deps only

# copy source AFTER deps for better caching
COPY . .

# compile TypeScript ➔ dist/
RUN npm run build

CMD ["node", "dist/index.js"]
