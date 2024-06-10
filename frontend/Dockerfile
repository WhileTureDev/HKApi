# Build stage
FROM node:22.2.0-alpine AS build
WORKDIR /app

COPY nextjs-dashboard/ .

# Install next as a production dependency
RUN npm i


CMD ["npm", "run", "dev"]
