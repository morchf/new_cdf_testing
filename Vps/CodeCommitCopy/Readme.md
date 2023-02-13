Upgrade.py -----
This python script accepts one argument which is Version no. Script can only be used to upgrade all VPS at once. If you want to upgrade just some number of VPS then that can be done through existing UpgradeVps.py VPS Upgrade . 


To upgrade all VPS at once, run this:  


python3 upgrade.py {version number}
ex: python3 upgrade.py 10.04.006
Upgrade.py script internally invokes UpgradeVps.py to upgrade all VPS with the given version.

This upgrade.py script only facilitates upgrading of the version i.e. from current to latest one. If user wants to downgrade the version, Lets say if current version is 10.06.008 and you want to rollback to some older version i.e. 10.04.006. Then push this older version with ‘latest’ tag in ECR (gtt/vps) repo. In this case, the command would be “python3 upgrade.py latest”.