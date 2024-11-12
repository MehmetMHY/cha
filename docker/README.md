# Cha - Docker

## Overview

Run Cha using Docker to access the CLI tool via your browser. This is useful if you prefer not to install all dependencies or are using Windows.

## Setup Instructions

1. Configure your **.env** file with the necessary API keys. See Cha's main README for details on required keys.

2. Load your **.env** file:

   ```bash
   # If the file is in the current directory
   source ./.env

   # If the file is in the root Cha directory
   source ../.env
   ```

3. Build the Docker image:

   ```bash
   docker build -t gotty-term .
   ```

4. Run the Docker image as a container:

   ```bash
   docker run -it -p 8080:8080 \
       -e OPENAI_API_KEY \
       -e BRAVE_API_KEY \
       gotty-term
   ```

5. Open your browser and go to: [http://localhost:8080/](http://localhost:8080/)

6. Once opened, you should see a bash terminal. Run Cha from there:

   ```bash
   cha
   ```
