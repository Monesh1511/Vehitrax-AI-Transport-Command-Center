FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
# Run npm install inside the container so native binaries match the musl/linux architecture
RUN npm install
# Copy source code (node_modules from host is excluded via .dockerignore)
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
