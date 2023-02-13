all: package

validate:
	sam validate
	cfn-lint -t Template.yml

package: validate
	mkdir -p Output
	@echo "Enter Deployment Bucket Name: "; \
	read DEPLOYMENTBUCKET; \
	sam build -t Template.yml; \
	aws cloudformation package --template-file .aws-sam/build/template.yaml --s3-bucket $$DEPLOYMENTBUCKET --output-template-file Output/output-template.yml
	aws cloudformation validate-template --template-body file://Output/output-template.yml 1> Output/validation-results.json

deploy: package validate
	@echo "Enter S3 Storage Bucket: "; \
	read S3STORAGEBUCKET; \
	sam deploy --region us-east-1 --template-file Output/output-template.yml --stack-name RetrieveOpticomLogs --capabilities CAPABILITY_NAMED_IAM --parameter-overrides S3StorageBucket=$$S3STORAGEBUCKET --no-fail-on-empty-changeset
