This Lambda requires files from the aws-cert-auth directory to function. 
Those files are copied in by the deploy_populate-cdf.py file. 

When creating cloudformation or otherwise loading to AWS, include all 
of the aws-cert-auth directory in the same directory as this populate-cdf.py.

The aws-cert-auth code requires the requests library.