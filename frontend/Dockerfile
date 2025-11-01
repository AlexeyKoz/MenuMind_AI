# Production Dockerfile for React Frontend
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code and config
COPY . .

# Override .env.production with localhost URLs for Docker
RUN echo "REACT_APP_API_URL=http://localhost:8000" > .env.production && \
    echo "REACT_APP_WS_URL=ws://localhost:8001" >> .env.production && \
    echo "REACT_APP_GOOGLE_CLIENT_ID=819829561375-19d74oa53gsn83r0qaaavb0659hsegqo.apps.googleusercontent.com" >> .env.production && \
    echo "GENERATE_SOURCEMAP=false" >> .env.production

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration (from builder stage where we copied everything)
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf

# Create nginx cache directories
RUN mkdir -p /var/cache/nginx/client_temp && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

