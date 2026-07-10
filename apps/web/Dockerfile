# ---- Build stage -----------------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app

# Install deps first for better layer caching.
COPY package.json package-lock.json* ./
RUN npm ci 2>/dev/null || npm install

COPY . .

# VITE_API_BASE is baked in at build time. When served behind nginx, we proxy
# /v1 etc. to the backend, so leaving it empty (relative requests) is correct.
ARG VITE_API_BASE=""
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

# ---- Serve stage -----------------------------------------------------------
FROM nginx:1.27-alpine AS serve

# Backend host the nginx proxy forwards API traffic to. Override at runtime:
#   docker run -e BACKEND_URL=http://api:8000 ...
ENV BACKEND_URL=http://localhost:8000

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# nginx:alpine's entrypoint renders /etc/nginx/templates/*.template with envsubst
# (using $BACKEND_URL) before starting nginx.
