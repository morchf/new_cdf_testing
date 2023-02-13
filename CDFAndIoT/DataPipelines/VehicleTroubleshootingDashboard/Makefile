all: package

validate:
	sam validate -t Template.yml
	cfn-lint -t Template.yml

package: validate
	mkdir -p Output
	@echo "Enter Deployment Bucket Name: "; \
	read DEPLOYMENTBUCKET; \
	sam build -t Template.yml; \
	aws s3 cp pyarrow-2.0-py3.7.egg s3://$$DEPLOYMENTBUCKET; \
	aws cloudformation package --template-file .aws-sam/build/template.yaml --s3-bucket $$DEPLOYMENTBUCKET --output-template-file Output/output-template.yml
	aws cloudformation validate-template --template-body file://Output/output-template.yml 1> Output/validation-results.json

deploy: package validate
	@echo "Enter Deployment Stack Name: "; \
	read STACKNAME; \
	echo "Enter Deployment Stack Region: "; \
	read STACKREGION; \
	echo "Enter Deployment Environment (contractor, act or production): "; \
	read DEPLOYMENTENVIRONMENT; \
	echo "Enter S3 Data Pipeline Bucket: "; \
	read S3PIPELINEBUCKET; \
	echo "Enter Glue Job Name: "; \
	read GLUEJOBNAME; \
	echo "Enter Quicksight Dashboard Name: "; \
	read QUICKSIGHTDASHBOARD; \
	echo "Enter Quicksight Dataset Name: "; \
	read QUICKSIGHTDATASET; \
	echo "Enter Deployment Bucket Name: "; \
	read DEPLOYMENTBUCKET; \
	echo "Enter CDF Endpoint: "; \
	read CDFENDPOINT; \
	sam deploy --region $$STACKREGION --template-file Output/output-template.yml --stack-name $$STACKNAME --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --parameter-overrides DeploymentEnvironment=$$DEPLOYMENTENVIRONMENT S3DataPipelineBucket=$$S3PIPELINEBUCKET GlueJobName=$$GLUEJOBNAME QuicksightDashboardName=$$QUICKSIGHTDASHBOARD QuicksightDatasetName=$$QUICKSIGHTDATASET DeploymentBucket=$$DEPLOYMENTBUCKET CDFEndpoint=$$CDFENDPOINT --no-fail-on-empty-changeset