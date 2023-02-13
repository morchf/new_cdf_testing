all: package

test:
	sed 's/REPLACE_S3_DEPLOYMENT_BUCKET/HelloWorld/g' template.yml > processed_template.yml

validate:
	sam validate -t template.yml
	cfn-lint -t template.yml
	# cfn_nag -i template.yml --output-format json | C:/src/jq-win64.exe '.[].file_results.failure_count' | grep -q '0'

package: validate
	mkdir -p Output
	@echo "Enter Deployment Bucket Name: "; \
	read DEPLOYMENTBUCKET; \
	aws s3 cp VehicleDataDecoders/VehicleDataDecoders.zip s3://$$DEPLOYMENTBUCKET; \
	aws cloudformation package --template-file template.yml --s3-bucket $$DEPLOYMENTBUCKET --output-template-file Output/output-template.yml
	echo "aws s3 cp VehicleDataDecoders/VehicleDataDecoders.zip s3://$$DEPLOYMENTBUCKET"
	aws cloudformation validate-template --template-body file://Output/output-template.yml 1> Output/validation-results.json

deploy: package validate
	@echo "Enter Deployment Stack Name: "; \
	read STACKNAME; \
	echo "Enter Deployment Stack Region: "; \
	read STACKREGION; \
	echo "Enter Deployment Bucket Name (Again): "; \
	read DEPLOYMENTBUCKET; \
	echo "Enter Name of The S3 Buckets to Create: "; \
	read DATABUCKET; \
	sam deploy --region $$STACKREGION --template-file Output/output-template.yml --stack-name $$STACKNAME --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --parameter-overrides DeploymentBucket=$$DEPLOYMENTBUCKET S3Bucket=$$DATABUCKET --no-fail-on-empty-changeset
