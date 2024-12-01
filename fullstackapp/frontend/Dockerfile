# Stage 1: Build Angular App
FROM node:18-alpine AS build

# Set working directory
WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application source
COPY . .

# Build the Angular app
RUN npm run build --omit=dev


# Stage 2: Serve Angular App with Nginx
FROM nginx:alpine AS production

# Copy built Angular app from Stage 1
COPY --from=build /usr/src/app/dist /usr/share/nginx/html

# Copy custom nginx configuration (optional)
# If needed, create a nginx.conf file in the frontend directory
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
