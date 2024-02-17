# Use an official Node.js runtime as the parent image
FROM node:14

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install project dependencies
RUN npm install

# Copy the rest of your project's files into the container
COPY . .

# Make port 3000 available outside this container
EXPOSE 3000

# Run the app using npm start
CMD ["npm", "start"]
