# Stage 1: Build the React Application
FROM node:18-alpine AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy dependency tracking lists
COPY package*.json ./

# Install exact node modules dependencies
RUN npm ci

# Copy the entire frontend source code
COPY . .

# Build the production bundle
RUN npm run build

# Stage 2: Serve the Static Assets using lightweight Nginx
FROM nginx:alpine

# Copy built frontend assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx routing configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose Nginx port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
