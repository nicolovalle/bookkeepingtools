#!/usr/bin/env python3

"""

rundiagnostics.py

Usage: ./rundiagnostics.py -f <firstrun> -l <lastrun> [--duration <min_duration>] [--run <option>] [--save]

Options:
    -h --help                  Display this help
    -f <firstrun>              First run number
    -l <lastrun>               Last run number 
    --duration <min_duration>  Min duration in minutes [default: -1]
    --run <option>             Option [default: timetable]
    --save                     Save figure as png [default: False]

* run options: timetable, eor, mdquality
* --duration used only for mdquality mode
"""


import requests
import json
import docopt
import re
import datetime
import tasks as task




argv = docopt.docopt(__doc__,version="1.0")
FromRun = int(argv['-f'])
ToRun = int(argv['-l'])
SavePng = bool(argv['--save'])
RunOption = str(argv['--run'])
MinDuration = float(argv['--duration'])

   
        
        
#______________________________________________________________
if __name__ == "__main__":
    fillNumbers_int = [int(n) for n in range(FromRun, ToRun+1)]
    fillNumbers_str = [str(n) for n in range(FromRun, ToRun+1)]
    fillNumbers_str_comma = ','.join(fillNumbers_str)
    print('ANALYZING RUNS',fillNumbers_str_comma);
    req = requests.get('https://ali-bookkeeping.cern.ch/api/runs?filter[runNumbers]={0}&page[offset]=0&page[limit]=999'.format(fillNumbers_str_comma),verify=False)
    #req = requests.get('https://ali-bookkeeping.cern.ch/api/runs',verify=False)
    data = json.loads(req.text)['data']
    data.reverse()
    filename = 'ALICE_run_from_{0}_to_{1}.json'.format(FromRun, ToRun);
    with open (filename, 'w') as f:
        json.dump(data, f, indent=2)

    print('DOWNLOADED:',len(data),'RUNS')
    if RunOption == 'timetable':
        task.TIMETABLE(data,SavePng)
    if RunOption == 'eor':
        task.EOR(data,SavePng)
    if RunOption == 'mdquality':
        task.MDQUALITYTABLE(data,MinDuration)

    
   
