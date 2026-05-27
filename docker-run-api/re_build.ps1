docker-compose stop api
docker-compose rm -f api
docker-compose build --no-cache
docker-compose up