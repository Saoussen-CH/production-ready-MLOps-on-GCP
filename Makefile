-include env.sh
export

help: ## Display this help screen
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Set up local Python environment for development.
	@echo "################################################################################" && \
	echo "# Install Python dependencies" && \
	echo "################################################################################" && \
	cd pipelines && \
	poetry install --with dev && \
	cd ../components && \
	poetry install --with dev

compile: ## Compile pipeline. Set pipeline=<training|prediction>.
	@echo "################################################################################" && \
	echo "# Compile pipeline" && \
	echo "################################################################################" && \
	cd pipelines/src && \
	poetry run python -m pipelines.training.pipeline

build: ## Build and push container.
	@echo "################################################################################" && \
	echo "# Build training image" && \
	echo "################################################################################" && \
	cd model && \
	docker build -t ${CONTAINER_IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
	docker push ${CONTAINER_IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

compile ?= true
build ?= true
run: ## Run a pipeline. Optionally set compile=<true|false> (default=true), build=<true|false>.
	@if [ $(compile) = "true" ]; then \
		$(MAKE) compile ; \
	elif [ $(compile) != "false" ]; then \
		echo "ValueError: compile must be either true or false" ; \
		exit ; \
	fi && \
	if [ $(build) = "true" ]; then \
		$(MAKE) build ; \
	elif [ $(build) != "false" ]; then \
		echo "ValueError: build must be either true or false" ; \
		exit ; \
	fi && \
	echo "################################################################################" && \
	echo "# Run training pipeline" && \
	echo "################################################################################" && \
	cd pipelines/src && \
	poetry run python -m pipelines.training.utils.trigger_pipeline --template_path=./taxifare-pipeline.yaml
