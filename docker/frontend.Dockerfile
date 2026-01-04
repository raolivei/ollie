# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package.json ./

# Install dependencies
RUN npm install

# Copy source files
COPY frontend/ .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

