default: start

TAG := $(shell cat package.json | jq -r .version)
MACHINE := clashleaders20

.PHONY: deploy
deploy:
	eval $$(docker-machine env $(MACHINE) --shell bash); docker pull amir20/clashleaders:$(TAG)
	eval $$(docker-machine env $(MACHINE) --shell bash); docker pull amir20/imgproxy-cache:$(TAG)
	eval $$(docker-machine env $(MACHINE) --shell bash); TAG=$(TAG) docker stack deploy -c docker-compose.yml -c docker-compose.production.yml clashleaders

.PHONY: build
build:
	TAG=$(TAG) docker compose -f docker-compose.yml build --build-arg SOURCE_COMMIT=$$(git rev-parse --short HEAD)
	docker tag amir20/clashleaders:$(TAG) amir20/clashleaders:latest

.PHONY: push
push: build
	docker push amir20/clashleaders:$(TAG)
	docker push amir20/imgproxy-cache:$(TAG)

.PHONY: test
test: build
	TAG=$(TAG) docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm test

.PHONY: start
start:
	@npm start

.PHONY: release_patch
release_patch:
	@npm version patch

.PHONY: release_minor
release_minor:
	@npm version minor

.PHONY: int
int:
	docker compose -f docker-compose.yml -f docker-compose.test.yml rm -fsv web
	TAG=$(TAG) docker compose -f docker-compose.yml -f docker-compose.test.yml build
	TAG=$(TAG) docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm integration
