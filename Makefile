.PHONY: install run test clean docker-build docker-run migrate

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

run:
	. venv/bin/activate && python manage.py runserver

migrate:
	. venv/bin/activate && python manage.py makemigrations && python manage.py migrate

test:
	. venv/bin/activate && python manage.py test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf venv/

docker-build:
	docker build -t kon-backend .

docker-run:
	docker run -p 8000:8000 --env-file .env kon-backend
