Objective: Removing Duplicate CDF entity templates :-

Each of the "smart-city-platform/CDFAndIoT/CDFInstallation/CDF/test/deploy/" and "CDF/cdf-tools/asslib/data/" directory
contains a copy of CDF entity templates, which is not being used for CDF installation.
To avoid having CDF templates at multiple locations, the two directories are zipped and moved to "Extras" folder.

The "smart-city-platform/CDFAndIoT/CDFInstallation/CDF/test/deploy/" directory is getting deprecated in CDF 3.0

The "smart-city-platform/CDF/cdf-tools/asslib/data/" directory has Python programs to show how to create, modify, and delete 
templates and instances for groups and devices. The alternative to these python programs is to use Postman.
