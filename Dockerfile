# Build stage for Next.js
FROM node:20-alpine AS frontend-builder

WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
# Create public dir if it doesn't exist
RUN mkdir -p public
RUN npm run build

# Production stage
FROM python:3.11-slim

# Install Node.js and ffmpeg
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml ./
COPY uv.lock ./

# Install uv and Python dependencies
RUN pip install uv && uv sync --frozen

# Copy the processor code
COPY processor/ ./processor/

# Create data directories (don't copy local data)
RUN mkdir -p data/books data/audio/sentences data/audio/chapters data/public/sentences data/public/chapters

# Copy built Next.js standalone app
COPY --from=frontend-builder /app/web/.next/standalone ./web
COPY --from=frontend-builder /app/web/.next/static ./web/.next/static
COPY --from=frontend-builder /app/web/public ./web/public

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Expose port
EXPOSE 3000

# Start the Next.js standalone server
WORKDIR /app/web
CMD ["node", "server.js"]
