# Easily Run Cha Docker

# global variables
IMAGE_NAME="gotty-term"
URL="http://localhost:8080/"

# ask user if they want to build the image
read -p "Do you want to build the Docker image? (yes/y): " build_image
build_image=$(echo "$build_image" | tr '[:upper:]' '[:lower:]')

# build the image if it does not exist or ask user to rebuild it
if [[ "$(docker images -q ${IMAGE_NAME} 2>/dev/null)" == "" || "$build_image" == "yes" || "$build_image" == "y" ]]; then
	if [[ "$(docker images -q ${IMAGE_NAME} 2>/dev/null)" != "" ]]; then
		echo "Removing existing ${IMAGE_NAME} image..."
		docker rmi -f ${IMAGE_NAME}
	fi
	echo "Building new ${IMAGE_NAME} image..."
	docker build --build-arg CACHE_DATE="$(date)" -t ${IMAGE_NAME} .
fi

# ask user if they want to open the application URL in the browser
read -p "Do you want to open the application URL in the browser? (yes/y): " open_url
open_url=$(echo "$open_url" | tr '[:upper:]' '[:lower:]')

# open link to instance in the browser if user agrees
if [[ "$open_url" == "yes" || "$open_url" == "y" ]]; then
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
