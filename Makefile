#This makefile handles the common commands from the project
TAG := $$(git rev-parse --short HEAD)

.PHONY: pull clean install tests run migrate collectstatic backend all

all: deps freeze migrate git run

pull:
	git fetch --all && git checkout ${GITHUB_REF_NAME} && git pull origin ${GITHUB_REF_NAME}

clean:
	sudo find . -type f -name '*.pyc' -delete
	sudo find . -type f -name '*.log' -delete
	prospector
		
install:
	pip3 install -r requirements.txt

tests:
	python3 manage.py test

last-tag:
	git describe --tags --abbrev=0

run:
	python3 manage.py runserver 8000

shell:
	python3 manage.py shell_plus

backend:
	python3 manage.py runserver 8080

migrate:
	python3 manage.py migrate

collectstatic:
	python3 manage.py collectstatic --noinput

docker-be:
	docker build -t backend:$(TAG) -f deploy/Dockerfile.colleges .


deps:
	pip install -r requirements.txt || true   # Install existing deps if file exists

freeze:
	pip freeze > requirements.txt
	echo "requirements.txt updated."

git:
	git add .
	git commit -m "Auto-update: deps, migrations, and preparations"
	git push

