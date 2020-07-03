STACK_NAME = trello-vertical-timeline

.PHONY: build-WebAppFunction
build-WebAppFunction:libpath = $(dir $(realpath $(ARTIFACTS_DIR)/../../../start.sh))lib
build-WebAppFunction:
	rsync -av --exclude=*__pycache__ --exclude=Makefile --exclude=static . $(ARTIFACTS_DIR)
	python -m pip install -r requirements.txt -t $(ARTIFACTS_DIR)
	python -m pip install $(libpath)/dynamodb-repository/ -t $(ARTIFACTS_DIR)
	python -m pip install $(libpath)/verticaltimeline-common/ -t $(ARTIFACTS_DIR)
	rm -rf $(ARTIFACTS_DIR)/bin
	rm -rf $(ARTIFACTS_DIR)/__pycache__

.PHONY: cdn
cdn:bucket = $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) \
	--query 'Stacks[0].Outputs[?OutputKey==`StaticFilesBucket`].OutputValue' \
	--output text)
cdn:
	aws s3 sync webapp/static/ s3://$(bucket)/ --delete --acl=public-read

.PHONY: freeze
freeze:
	pip freeze | grep -v -e "pkg-resources" -e "^-e git" > requirements.txt