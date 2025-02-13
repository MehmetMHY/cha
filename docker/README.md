# Cha - Docker

## Overview

Run Cha using Docker to access the CLI tool via your browser. This is useful if you prefer not to install all dependencies or are using Windows.

## How To Run (Easily Steps)

1. Make sure [Docker](https://www.docker.com/) is installed

2. Run the main run script (only run one of them):

   ```bash
   # run the docker container and build+run the image if it does not exist
   bash run.sh

   # same as the default option but open the link in the browser
   bash run.sh -o

   # same as the default option but rebuild the image
   bash run.sh -b

   # same as the default but rebuild the image and open the link in the browser
   bash run.sh -o -b
   ```

3. (NOTE) If this does not work, follow the steps below...

## Setup Instructions (MacOS & Linux)

1. Make sure [Docker](https://www.docker.com/) is installed

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

1. Make sure [Docker](https://www.docker.com/) is installed

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

## Use As Chrome Extension

1. Run the docker container for this project, follow the instructions above

2. Open up your instance of the Google Chrome Browser

3. Go to this url/setting: chrome://extensions/

4. Enable "Developer mode"

5. Click the "Load unpacked" button and load Cha's extension from the ./docker/chrome/ directory

6. Click the puzzle looking icon close to the top left corner of the browser and "pin" the "Cha" extension
