# Video-insights (Version A) - Node.js Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache python3 make g++

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Install runtime dependencies including ffmpeg for video processing
RUN apk add --no-cache python3 make g++ ffmpeg

# Install production dependencies (needed for external deps)
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

# Copy built application (server + client)
COPY --from=builder /app/dist ./dist

# Create uploads directory
RUN mkdir -p /app/uploads

ENV NODE_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["node", "dist/index.cjs"]
