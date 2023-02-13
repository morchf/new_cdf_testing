key="$jira"
value="$desc"
review="$review"
all:
	git status
	git checkout -b feature-$$jira
	git add .
	git commit -m "feature-$$jira $$value"
	git push -u origin feature-$$jira
	hub pull-request -m "feature-$$jira $$value" -r $$review
.PHONY : help
help :
	@echo "key	: jira ticket number (ex:- SCP-505 )"
	@echo "value	: jira ticket discription(case sensitive)"
	@echo "review	: list of reviewer github name (ex:- 'LSchiefel,gnatesan16' )"
	@echo "example	: make jira='SCP-101' desc='nothingnew' review='LSchiefel,gnatesan16'"
