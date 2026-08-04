# --- Stage 1: Build static assets ---
FROM node:18-alpine AS build

WORKDIR /app

# Copy dependency configs
COPY package.json package-lock.json ./
RUN npm ci

# Copy source files
COPY . .

# Build production bundle
RUN npm run build

# --- Stage 2: Serve using Nginx ---
FROM nginx:alpine

# Copy built assets to Nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
