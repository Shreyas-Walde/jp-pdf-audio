# Build stage for Next.js
FROM node:20-alpine AS frontend-builder

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN mkdir -p public
RUN npm run build

# Production stage
FROM node:20-slim

# Install Python and ffmpeg
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built Next.js app
COPY --from=frontend-builder /app/web ./web

# Create data directories
RUN mkdir -p data/books data/audio/sentences data/audio/chapters data/public/sentences data/public/chapters

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Expose port
EXPOSE 3000

# Start the Next.js server
WORKDIR /app/web
CMD ["npm", "run", "start"]
