# frontend/Dockerfile
FROM node:16.14.2-alpine
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
EXPOSE 3000
CMD ["npx", "serve", "build"]
