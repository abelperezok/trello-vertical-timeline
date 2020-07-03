libpath = $(dir $(realpath $(ARTIFACTS_DIR)/../../../template.yaml))lib

.PHONY: build-PopulateDataFunction
build-PopulateDataFunction:
	rsync -av --exclude=*__pycache__ --exclude=Makefile --exclude=static . $(ARTIFACTS_DIR)
	python -m pip install -r requirements.txt -t $(ARTIFACTS_DIR)
	python -m pip install $(libpath)/dynamodb-repository/ -t $(ARTIFACTS_DIR)
	python -m pip install $(libpath)/verticaltimeline-common/ -t $(ARTIFACTS_DIR)
	rm -rf $(ARTIFACTS_DIR)/bin
	rm -rf $(ARTIFACTS_DIR)/__pycache__

.PHONY: freeze
freeze:
	pip freeze | grep -v -e "pkg-resources" -e "^-e git" > requirements.txt