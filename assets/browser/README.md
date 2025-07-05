# Cha In The Browser

## Overview

Run Cha using Docker to access the CLI tool via your browser. This is useful if you prefer not to install all dependencies or are using Windows.

## How To Run (Easily Steps)

1. Make sure [Docker](https://www.docker.com/) is installed.

2. Run the main script:

   When you execute the script, you will be prompted to decide whether to build the Docker image and whether to open the application URL in your browser. Enter "yes" or "y" to proceed with these actions.

   ```bash
   # run the docker container, with optional image build and URL opening based on user input
   bash run.sh
   ```

3. (NOTE) If this does not work, follow the steps below...

## Setup Instructions (MacOS & Linux)

1. Make sure [Docker](https://www.docker.com/) is installed.

2. Configure your **.env** file with the necessary API keys. See Cha's main README for details on required keys.

3. Load your **.env** file:

   ```bash
   # If the file is in the current directory
   source ./.env

   # If the file is in the root Cha directory
   source ../.env
   ```

4. Build the Docker image:

   ```bash
   docker build -t gotty-term .
   ```

5. Run the Docker image as a container:

   ```bash
   docker run -it -p 8080:8080 \
       -e OPENAI_API_KEY \
       gotty-term
   ```

6. Open your browser and go to: [http://localhost:8080/](http://localhost:8080/)

7. Once opened, you should see a bash terminal. Run Cha from there:

   ```bash
   cha
   ```

## Setup Instructions (Windows)

1. Make sure [Docker](https://www.docker.com/) is installed.

2. Build the Docker image:

   ```bash
   docker build -t gotty-term .
   ```

3. Run the Docker image as a container:

   - This is NOT secure but this is the easiest way to run this in Windows; ya Windows should have been Unix based lol

   ```bash
   # NOTE: enter your environment variables here!
   docker run -it -p 8080:8080 `
       -e "OPENAI_API_KEY=<your_openai_api_key>" `
       gotty-term
   ```

4. Open your browser and go to: [http://localhost:8080/](http://localhost:8080/)

5. Once opened, you should see a bash terminal. Run Cha from there:

   ```bash
   cha
   ```
