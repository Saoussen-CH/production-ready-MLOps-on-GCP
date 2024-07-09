export VERTEX_PROJECT_ID=mlops-learning-422012
export VERTEX_LOCATION=us-central1
export BQ_LOCATION=US

export BUCKET_NAME=mlops_pipeline_t
export BUCKET_URI=gs://${BUCKET_NAME}

export CONTAINER_IMAGE_REGISTRY=${VERTEX_LOCATION}-docker.pkg.dev/${VERTEX_PROJECT_ID}/mlops-docker-repo
export IMAGE_NAME=taxifare_training_container
export IMAGE_TAG=v1
