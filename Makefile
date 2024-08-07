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
	echo "# Compile $$pipeline pipeline" && \
	echo "################################################################################" && \
	cd pipelines/src && \
	poetry run python -m pipelines.${pipeline}

build: ## Build and push container.
	@echo "################################################################################" && \
	echo "# Build training image" && \
	echo "################################################################################" && \
	cd model && \
	docker build -t ${VERTEX_LOCATION}-docker.pkg.dev/${VERTEX_PROJECT_ID}/mlops-docker-repo/${IMAGE_NAME}:${IMAGE_TAG} .
	docker push ${VERTEX_LOCATION}-docker.pkg.dev/${VERTEX_PROJECT_ID}/mlops-docker-repo/${IMAGE_NAME}:${IMAGE_TAG}

compile ?= true
build ?= true
enable_caching ?= false
run: ## Run a pipeline. Set pipeline=<training|prediction>. Optionally set compile=<true|false> (default=true), build=<true|false>, enable_caching=<true|false> (default=false).
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
	if [ $(enable_caching) != "true" ] && [ $(enable_caching) != "false" ]; then
		echo "ValueError: enable_caching must be either true or false" ;
		exit ;
	fi && \
	echo "################################################################################" && \
	echo "# Run $$pipeline pipeline" && \
	echo "################################################################################" && \
	cd pipelines/src && \
	poetry run python -m pipelines.utils.trigger_pipeline --template_path=./taxifare-${pipeline}-pipeline.yaml --display_name=taxifare-${pipeline}-pipeline --type=${pipeline} --enable_caching=${enable_caching}

training: ## Run training pipeline. Supports same options as run.
	@$(MAKE) run pipeline=training

prediction:	## Run prediction pipeline. Supports same options as run.
	@$(MAKE) run pipeline=prediction build=false

test-components: ## Run unit tests for components package
	@echo "################################################################################" && \
	echo "# Test components package" && \
	echo "################################################################################" && \
	echo "Testing components package" && \
	cd components && \
	poetry run pytest

test-pipelines: ## Run unit tests for pipelines package
	@echo "################################################################################" && \
	echo "# Test pipelines package" && \
	echo "################################################################################" && \
	echo "Testing pipelines package" && \
	cd pipelines/tests && \
	poetry run pytest utils/test_trigger_pipelines.py &&\
	poetry run pytest utils/test_upload_pipeline.py


e2e-tests: ##Perform end-to-end (E2E) pipeline tests. Must specify pipeline=<training|prediction>.
	cd pipelines && \
	poetry run pytest tests/test_e2e.py --pipeline_type=${pipeline}

setup-backend:
	@echo "Setting up backend for environments $(project_id)"
	@cd terraform/backend && \
	terraform init && \
	terraform plan  -var 'project_id=${project_id}' -out=plan.out && \
	if [ -s plan.out ]; then \
		echo "Changes detected. Applying the plan for the project"; \
		terraform apply -auto-approve "plan.out";  \
	else \
		echo "No changes detected. Skipping apply for project"; \
	fi; \
	rm -f plan.out; \
