.PHONY: install notebooks run clean container container-run

IMAGE_NAME ?= embeddings-workshop
CONTAINER_TOOL ?= docker

install:
	pip install -r requirements.txt

run:
	jupyter lab notebooks/

clean:
	rm -f notebooks/*.ipynb

container-build:
	$(CONTAINER_TOOL) build \
	  --file embeddings.containerfile \
	  --tag $(IMAGE_NAME) .

container-run: container-build
	mkdir -p outputs
	$(CONTAINER_TOOL) run --rm -it \
	  --publish 8888:8888 \
	  --volume "$(CURDIR)/notebooks":/app/notebooks \
	  --volume "$(CURDIR)/data":/app/data \
	  --volume "$(CURDIR)/outputs":/app/outputs \
	  $(IMAGE_NAME)
