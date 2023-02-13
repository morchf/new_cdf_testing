2100 Simulator Data File Generator

Usage: python DataFiles2100.py [options] [args]

This function creates data files for 2100 Simulation and places them in the folder "Output".  To use this function specify "python 2100Simulator.py" followed by any optional arguments then the two required arguments.

Options:
    -h, --help          show this message and exit
    -c, --class         set the class of the vehicles in the data files, expects a single integer.  Default value is 10
    -a, --agency        set the agency id (city id) of the vehicles in the data files, expects a single integer.  Default Value is 0
    -i, --ids           set the vehicle ids to create data files for, expects a comma delimited list of integers or integer ranges denoted by a "-".  The integer ranges are inclusive of the end points.  For example this argument may look like "--ids 2991,2902-2979,3000-3296,3700-3823"
    -id-file            reads the ids from a CDF CSV file and uses them in place of the "--ids" option.  Should be a path to the CDF CSV file
    -p, --priority      set the priority level of all the vehicles.  Must be an integer or one of "High", "Low", "Probe", "Disabled", "Mapping", "Transit", "UNK_6", or "UNK_7"
    -o, --opstatus      set the opstatus level of all the vehicles.  Must be an integer or one of "Priority Disabled", "Priority Enabled", "Mapping?", "Manual", "Diag Channel A", "Diag Channel B", "Diag Channel C", or "Diag Channel D"
    -t, --turn          set the turn level of all the vehicles. Must be an integer or one of "Straight", "Left", "Right", or "UNK_3"
    --data-files-only   only create data files and do not publish to the endpoint
    -e, --endpoint      url or hostname of the endpoint where the MQTT messages will be published
    --cert              path to the certificate file of the client
    --rootca            path to the root ca to use when connecting
    --key               path to the private key of the client
    -g, --agency-guid   agency guid to publish messages under

Arguments:
    The name of or a list of log files that the data files will be created from.  They should be of the format "filename=count" to denote how many vehicles to use that log file.  If you wish for all of the rest of the vehicles to use that file then the "=" and the count should be omitted.  For example the arguments may be written as "LogFiles/GTTAroundOffice.log=50 LogFiles/EastBound.log=5 LogFiles/WestBound.log"

    All of the commandline options can also be set through the config file at "Config.py".  

Example:
    python .\Simulator2100.py --class 10 --agency 65 --data-files-only --ids 2991,2902-2960 LogFiles/Output/intersection0.log=15 LogFiles/Output/intersection1.log=15 LogFiles/Output/intersection2.log=15 LogFiles/Output/intersection3.log=15

    python .\Simulator2100.py --class 10 --agency 65 --data-files-only --ids 2991,2902-2950 LogFiles/Output/intersection0.log=1 LogFiles/Output/intersection1.log=1 LogFiles/Output/intersection2.log=1 LogFiles/Output/intersection3.log=1 LogFiles/Output/intersection4.log=1 LogFiles/Output/intersection5.log=1 LogFiles/Output/intersection6.log=1 LogFiles/Output/intersection7.log=1 LogFiles/Output/intersection8.log=1 LogFiles/Output/intersection9.log=1 LogFiles/Output/intersection10.log=1 LogFiles/Output/intersection11.log=1 LogFiles/Output/intersection12.log=1 LogFiles/Output/intersection13.log=1 LogFiles/Output/intersection14.log=1 LogFiles/Output/intersection15.log=1 LogFiles/Output/intersection16.log=1 LogFiles/Output/intersection17.log=1 LogFiles/Output/intersection18.log=1 LogFiles/Output/intersection19.log=1 LogFiles/Output/intersection20.log=1 LogFiles/Output/intersection21.log=1 LogFiles/Output/intersection22.log=1 LogFiles/Output/intersection23.log=1 LogFiles/Output/intersection24.log=1 LogFiles/Output/intersection25.log=1 LogFiles/Output/intersection26.log=1 LogFiles/Output/intersection27.log=1 LogFiles/Output/intersection28.log=1 LogFiles/Output/intersection29.log=1 LogFiles/Output/intersection30.log=1 LogFiles/Output/intersection31.log=1 LogFiles/Output/intersection32.log=1 LogFiles/Output/intersection33.log=1 LogFiles/Output/intersection34.log=1 LogFiles/Output/intersection35.log=1 LogFiles/Output/intersection36.log=1 LogFiles/Output/intersection37.log=1 LogFiles/Output/intersection38.log=1 LogFiles/Output/intersection39.log=1 LogFiles/Output/intersection40.log=1 LogFiles/Output/intersection41.log=1 LogFiles/Output/intersection42.log=1 LogFiles/Output/intersection43.log=1 LogFiles/Output/intersection44.log=1 LogFiles/Output/intersection45.log=1 LogFiles/Output/intersection46.log=1 LogFiles/Output/intersection47.log=1 LogFiles/Output/intersection48.log=1 LogFiles/Output/intersection49.log=1
