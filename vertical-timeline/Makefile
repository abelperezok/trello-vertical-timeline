S3_BUCKET_WEB = hello-sam-flask-staticfilesbucket-6b0uhnylm4f5

build-WebAppFunction:
	echo "Hello custom build"
	rsync -av --exclude=*__pycache__ --exclude=Makefile --exclude=static . $(ARTIFACTS_DIR)
	python -m pip install -r requirements.txt -t $(ARTIFACTS_DIR)
	rm -rf $(ARTIFACTS_DIR)/bin
	rm -rf $(ARTIFACTS_DIR)/__pycache__
	aws s3 sync webapp/static/ s3://$(S3_BUCKET_WEB)/ --delete --acl=public-read