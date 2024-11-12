# Easily Run Cha Docker

# global variables
IMAGE_NAME="gotty-term"
URL="http://localhost:8080/"

# build the image if it does not exist or ask to user to rebuild it
if [[ "$(docker images -q ${IMAGE_NAME} 2>/dev/null)" == "" ]]; then
	echo "Docker image ${IMAGE_NAME} does not exist. Building it now."
	docker build -t ${IMAGE_NAME} .
else
	echo "Do you want to rebuild it? (y/N): "
	read build_image

	build_image=$(echo "$build_image" | tr '[:upper:]' '[:lower:]')
	if [[ "$build_image" == "y" ]]; then
		docker build -t ${IMAGE_NAME} .
	fi
fi

# open link to instance in the browser
if [[ "$OSTYPE" == "darwin"* ]]; then
	open $URL
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
	xdg-open $URL
elif [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
	start $URL
else
	echo "Please open the following URL in your browser: $URL"
fi

# run the Docker container
docker run -it -p 8080:8080 \
	-e OPENAI_API_KEY \
	-e BRAVE_API_KEY \
	${IMAGE_NAME}
