#!/usr/bin/env python3

"""

rundiagnostics.py

Usage: ./rundiagnostics.py -f <firstrun> -l <lastrun> -t <token_file> [--duration <min_duration>] [--run <option>] [--save]

Options:
    -h --help                  Display this help
    -f <firstrun>              First run number
    -l <lastrun>               Last run number 
    -t <token_file>            Path to file with your bookkeeping token
    --duration <min_duration>  Min duration in minutes [default: -1]
    --run <option>             Option [default: timetable]
    --save                     Save figure as png [default: False]

* run options: timetable, eor, mdquality
* --duration used only for mdquality mode
"""

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


import requests
import json
import docopt
import re
import datetime
import tasks as task
import sys




argv = docopt.docopt(__doc__,version="1.0")
FromRun = int(argv['-f'])
ToRun = int(argv['-l'])
tokenfile = str(argv['-t'])
SavePng = bool(argv['--save'])
RunOption = str(argv['--run'])
MinDuration = float(argv['--duration'])

   
def isReadable(run):
    checks = ['nDetectors','runType']
    for c in checks:
        if run[c] is None:
            return False
    return True
    
        
#______________________________________________________________
if __name__ == "__main__":
    runNumbers_int = [int(n) for n in range(FromRun, ToRun+1)]
    runNumbers_str = [str(n) for n in range(FromRun, ToRun+1)]
    runNumbers_str_comma = ','.join(runNumbers_str)
    print('ANALYZING RUNS',runNumbers_str_comma);
    with open(tokenfile,'r') as f:
        tok = f.readline().strip()
    req = requests.get('https://ali-bookkeeping.cern.ch/api/runs?filter[runNumbers]={0}&page[offset]=0&page[limit]=999&token={1}'.format(runNumbers_str_comma,tok),verify=False)
    #req = requests.get('https://ali-bookkeeping.cern.ch/api/runs',verify=False)
    print(req)
    data = json.loads(req.text)['data']
    data.reverse()
    print('Downloaded',len(data),'runs')
    data = [r for r in data if isReadable(r)]
    print('Readable runs:',len(data))
    filename = 'ALICE_run_from_{0}_to_{1}.json'.format(FromRun, ToRun);
    
    with open (filename, 'w') as f:
        json.dump(data, f, indent=2)

    if RunOption == 'timetable':
        task.TIMETABLE(data,SavePng)
    if RunOption == 'eor':
        task.EOR(data,SavePng)
    if RunOption == 'mdquality':
        task.MDQUALITYTABLE(data,MinDuration)

    
   
