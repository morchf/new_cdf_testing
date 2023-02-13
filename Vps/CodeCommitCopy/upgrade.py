#!/usr/bin/env python
import sys
import subprocess
import fileinput

version_name = sys.argv[1]
bash_command = "docker ps --format {{.Names}}={version_name} > upgrade_all.sh"
s = subprocess.run(bash_command, shell=True)
subprocess.call(["sed", "-i", "/.*ecs-agent.*/d", "upgrade_all.sh"])
for line in fileinput.input(["./upgrade_all.sh"], inplace=True):
    sys.stdout.write("python3 UpgradeVps.py {l}".format(l=line))

for line in fileinput.input(["./upgrade_all.sh"], inplace=True):
    line = line.replace("{version_name}", f"{version_name}")
    sys.stdout.write(line)

subprocess.call(["sh", "./upgrade_all.sh"])
