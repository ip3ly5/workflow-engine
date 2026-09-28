COMPOSE = docker compose -f docker-compose.dev.yml --env-file ./backend/.env.development

test:
	$(COMPOSE) run --build --rm backend python manage.py test $(args)
