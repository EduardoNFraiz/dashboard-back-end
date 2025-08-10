up:
	docker-compose up
stop:
	docker-compose stop	
build:
	docker-compose up --build
down:
	docker-compose down
destroy:
	docker-compose down -v
superuser:
	sh ./create_superuser.sh

