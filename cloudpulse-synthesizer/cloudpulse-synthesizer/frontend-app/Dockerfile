FROM node:20-alpine AS build
WORKDIR /app

# Copy dependency definitions
COPY package*.json ./
RUN npm install

# Copy source files and build
COPY . .
RUN npm run build

# Step 2: Serve the app with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]