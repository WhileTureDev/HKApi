# Set the base image. This image includes Node.js and npm.
FROM node:22.2.0

# Set the working directory in the Docker container
WORKDIR /app

# Copy the package.json and package-lock.json files into the container
COPY hkui/package*.json ./

# Install the dependencies in the container
RUN npm install

# Copy all files from your local workspace into the Docker container
COPY hkui/ .

# Expose the port 3000 to be able to access the app
EXPOSE 3000

# Start the application
CMD ["npm", "start"]