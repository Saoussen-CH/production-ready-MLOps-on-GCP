FROM us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-11.py310:latest

# Installs hypertune library
RUN pip install cloudml-hypertune

COPY . /code

WORKDIR /code

ENTRYPOINT ["python3", "-m", "trainer.task"]
