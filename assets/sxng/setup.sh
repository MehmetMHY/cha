# default values
DEFAULT_PORT=8080
DEFAULT_NAME="my-instance"
DEFAULT_URL="http://localhost"

# set instance's port number
read -p "Enter port (default $DEFAULT_PORT): " PORT
PORT=${PORT:-$DEFAULT_PORT}

# set instance's name
read -p "Enter instance name (default $DEFAULT_NAME): " NAME
NAME=${NAME:-$DEFAULT_NAME}

# set instance's base URL
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
read -p "Do you want to update the searxng image? (y/n): " UPDATE
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

# print details
echo "SearXNG instance '$NAME' is running on ${BASE_URL}:${PORT}"
