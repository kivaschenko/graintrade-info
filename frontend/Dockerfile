# Stage 1: Build stage
FROM node:18-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package.json package-lock.json ./

# Install all dependencies (including devDependencies)
RUN npm install --ignore-scripts && npm cache clean --force

# Copy the rest of the application code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Production stage
FROM nginx:stable-alpine

# Copy the built app from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose the application port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]

# Use a health check to ensure the server is running
HEALTHCHECK CMD curl --fail http://localhost:80/ || exit 1