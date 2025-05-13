# default values
DEFAULT_PORT=8080
DEFAULT_NAME="my-instance"
DEFAULT_URL="http://localhost"

# prompt for user input
read -p "Enter port (default $DEFAULT_PORT): " PORT
PORT=${PORT:-$DEFAULT_PORT}

read -p "Enter instance name (default $DEFAULT_NAME): " NAME
NAME=${NAME:-$DEFAULT_NAME}

read -p "Enter base URL (default $DEFAULT_URL): " BASE_URL
BASE_URL=${BASE_URL:-$DEFAULT_URL}

# check if an instance is already running on the specified port
if docker ps -q -f "publish=$PORT" | grep -q .; then
	read -p "An instance is already running on port $PORT. Stop it? (y/n): " STOP
	if [[ $STOP == "y" ]]; then
		docker stop $(docker ps -q -f "publish=$PORT")
	else
		echo "Exiting without changes."
		exit 0
	fi
fi

# ask about updating the image
read -p "Do you want to update the searxng/searxng image? (y/n): " UPDATE
if [[ $UPDATE == "y" ]]; then
	docker pull searxng/searxng
fi

# run the container
docker run --rm \
	-d -p ${PORT}:8080 \
	-v "${PWD}/searxng:/etc/searxng" \
	-e "BASE_URL=${BASE_URL}:${PORT}/" \
	-e "INSTANCE_NAME=${NAME}" \
	--name $NAME \
	searxng/searxng

echo "SearXNG instance '$NAME' is now running on ${BASE_URL}:${PORT}"
