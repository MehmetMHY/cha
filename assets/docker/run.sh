# Easily Run Cha Docker

# global variables
IMAGE_NAME="gotty-term"
URL="http://localhost:8080/"

# display help if -h parameter is passed
if [[ "$1" == "-h" || "$2" == "-h" ]]; then
	echo "Name: Cha Docker Setup Tool"
	echo "Usage: run.sh [options]"
	echo "Options:"
	echo "  -b  Rebuild the Docker image"
	echo "  -o  Open the application URL in the browser"
	echo "  -h  Display this help message"
	exit 0
fi

# build the image if it does not exist or ask to user to rebuild it
if [[ "$(docker images -q ${IMAGE_NAME} 2>/dev/null)" == "" ]]; then
	echo "Docker image ${IMAGE_NAME} does not exist. Building it now."
	docker build --build-arg CACHE_DATE="$(date)" -t ${IMAGE_NAME} .
else
	if [[ "$1" == "-b" || "$2" == "-b" ]]; then
		echo "Removing existing ${IMAGE_NAME} image..."
		docker rmi -f ${IMAGE_NAME}
		echo "Building new ${IMAGE_NAME} image..."
		docker build --build-arg CACHE_DATE="$(date)" -t ${IMAGE_NAME} .
	fi
fi

# open link to instance in the browser
if [[ "$1" == "-o" || "$2" == "-o" ]]; then
	if [[ "$OSTYPE" == "darwin"* ]]; then
		open $URL
	elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
		xdg-open $URL
	elif [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
		start $URL
	else
		echo "Please open the following URL in your browser: $URL"
	fi
fi

# run the Docker container
docker run -it -p 8080:8080 \
	-e OPENAI_API_KEY \
	${IMAGE_NAME}
