all: package

validate:
	sam validate -t Template.yml
	cfn-lint -t Template.yml

package: validate
	mkdir -p Output
	@echo "Enter Deployment Bucket Name: "; \
	read DEPLOYMENTBUCKET; \
	sam build -t Template.yml; \
	aws cloudformation package --template-file .aws-sam/build/template.yaml --s3-bucket $$DEPLOYMENTBUCKET --output-template-file Output/output-template.yml
	aws cloudformation validate-template --template-body file://Output/output-template.yml 1> Output/validation-results.json

deploy: package validate
	@echo "Enter Deployment Stack Name: "; \
	read STACKNAME; \
	echo "Enter Deployment Stack Region: "; \
	read STACKREGION; \
	echo "Enter Deployment Environment (contractor, act or production): "; \
	read DEPLOYMENTENVIRONMENT; \
	echo "Enter Quicksight Dashboard name: "; \
	read QUICKSIGHTDASHBOARD; \
	echo "Enter Quicksight Dataset name: "; \
	read QUICKSIGHTDATASET; \
	echo "Enter Quicksight User Arn: "; \
	read QUICKSIGHTUSER; \
	echo "Enter Data Viz Bucket Name: "; \
	read DATAVIZBUCKET; \
	echo "Enter CDF Endpoint Name: "; \
	read CDFENDPOINT; \
	sam deploy --region $$STACKREGION --template-file Output/output-template.yml --stack-name $$STACKNAME --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND --parameter-overrides DeploymentEnvironment=$$DEPLOYMENTENVIRONMENT QuicksightDashboardName=$$QUICKSIGHTDASHBOARD QuicksightDatasetName=$$QUICKSIGHTDATASET QuicksightUserArn=$$QUICKSIGHTUSER DataVizBucket=$$DATAVIZBUCKET CDFEndpoint=$$CDFENDPOINT --no-fail-on-empty-changeset
