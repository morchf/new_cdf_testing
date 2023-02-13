First edit the configure.json file by setting the name of the thing and any other relavent 
parameters such as mac address.

Next, execute the following command:
    python Setup.py setup

The 'setup' command creates a thing. Confirm the thing is created in the AWS Console.  Go to 
IoT Core->Manage->Things. A thing should exist that matches the 'thing_name' from the 
configure.json file. 

The 'setup' command creates a certificate. Confirm this by clicking on the 'thing_name' thing.
Then click on security in the left-pane navigation of the thing. All the certificates attached
to this particular thing are listed. More than one cert can be attached to a thing. 

The 'setup' command create a policy for the certificate. Confirm this by clicking on certificate of 
the thing. Then click on the policy in the left-pane navigation of the certificate. All policies 
associated with the certificate are listed. Click on the policy to view the specific policy. 

Another way to view the the certs are to go to IoT Core->Secure. All the certs that can be used by
real-world-physical-devices to connect to this endpoint are listed here. It is possible for a cert 
to exist without being attached to a thing. The policy allowed by a cert can be viewed by clicking
on the cert then viewing the policy.

Last, to cleanup (delete) the thing, cert, and policy enter the following command:
    python Setup.py cleanup
