import numpy as np
import pandas as pd
import requests
import json
import argparse
import docopt
import re
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import gridspec
from datetime import datetime
from datetime import date
import seaborn as sns


utctosec = 1./(1000)
utctoh = 1./(1000*60*60)
DETECTORS = ["STABLE BEAMS","CPV", "EMC", "FDD", "FT0", "FV0", "HMP", "ITS", "MCH", "MFT", "MID", "PHS", "TOF", "TPC", "TRD", "ZDC"]
#DETECTORS.reverse()

firsttimestamp = datetime.now()
firstmidnight = datetime.now()

foundUnknownRunType = False


def Toffset(ut):
    return (datetime.fromtimestamp(ut*utctosec) - firstmidnight).total_seconds()/3600


#______


def IsRunType(run,runtype):
    global foundUnknownRunType
    if runtype == 'SB':
        return False
    if runtype == "COSMICS" or runtype == "PHYSICS" or runtype == "TECHNICAL" or runtype == "SYNTHETIC":
        return run['runType']['name'] == runtype
    elif runtype == "CALIBRATION":
        return run['definition'] == runtype
    elif runtype == "unknown": 
        IsUnknown = not (IsRunType(run,"COSMICS") or IsRunType(run,"CALIBRATION") or IsRunType(run,"PHYSICS") or IsRunType(run,"TECHNICAL") or IsRunType(run,"SYNTHETIC"))
        if IsUnknown:
            foundUnknownRunType = True
            print('UNKNOWN RUN TYPE FOR RUN',run['runNumber'])
        return IsUnknown
    return True

def GetColMap(red, green, blue):
    return mpl.colors.LinearSegmentedColormap.from_list(str(red)+'-'+str(green)+'-'+str(blue),[(red/255,green/255,blue/255),(0,0,0)],N=2)

ColMaps = {'PHYSICS': GetColMap(72,212,36), 'COSMICS': GetColMap(229,232,147), 'SYNTHETIC': GetColMap(96,74,125), 'TECHNICAL': GetColMap(190,190,190), 'CALIBRATION': GetColMap(160,0,0), 'unknown': GetColMap(0,0,0), 'SB': GetColMap(255,0,0)} 


#___________________________________________________________
def TIMETABLE(data,SavePng):

    global firsttimestamp
    global firstmidnight
    global foundUnknownRunType

    binWidthTolerance = 0.002/3600
    
    utc0 = data[0]['startTime']
    firsttimestamp = datetime.fromtimestamp(utc0*utctosec)
    firstmidnight = firsttimestamp.replace(hour=0,minute=0,second=0)
    print(firstmidnight)
    X={}
    Y={}
    for runtype in ['COSMICS','SYNTHETIC','TECHNICAL','PHYSICS','CALIBRATION','unknown','SB']:
        X[runtype]=[]
        Y[runtype]=[]
        
    BinEdges_ = []
    minRunStart = 9999999
    for run in data:
        ndet = run['nDetectors']
        print(run['runNumber'],',',ndet,'detectors')
        #if (ndet < 2):
        #    continue
        BinEdges_.append(Toffset(run['startTime']))
        BinEdges_.append(Toffset(run['endTime']))
        minRunStart = min(minRunStart, Toffset(run['startTime']))
        sbfound = True
        try:
            if isinstance(run['lhcFill']['stableBeamsStart'],int) and isinstance(run['lhcFill']['stableBeamsStart'],int):
                BinEdges_.append(Toffset(run['lhcFill']['stableBeamsStart']))
                BinEdges_.append(Toffset(run['lhcFill']['stableBeamsEnd']))
        except:
            sbfound = False
    BinEdges_.sort()
    BinEdges_ = [e for e in BinEdges_ if e >= minRunStart] 
    
    BinEdges = [BinEdges_[0],]

    for i in range(1, len(BinEdges_)):
        if BinEdges_[i] - BinEdges[-1] >= binWidthTolerance:
            BinEdges.append(BinEdges_[i])

            
    for run in data:
        ndet = run['nDetectors']
        #if (ndet < 1):
        #    continue
        if 'TST' in run['detectors']:
            continue
        list_det = run['detectors'].split(',')
        if '' in list_det:
            continue
        list_det_id = [DETECTORS.index(idet) for idet in list_det]
        #print('RUN')
        #print(list_det_id)
        start_time = Toffset(run['startTime'])
        end_time = Toffset(run['endTime'])
        for ibin in [ib+binWidthTolerance/2 for ib in BinEdges if start_time <= ib < end_time]:
            for idet in list_det_id:
                for rtype in X:
                    if IsRunType(run,rtype):
                        #print(rtype)
                        X[rtype].append(ibin)
                        Y[rtype].append(idet)
        try:
            if isinstance(run['lhcFill']['stableBeamsStart'],int) and isinstance(run['lhcFill']['stableBeamsStart'],int):
                for ibin in [ib+binWidthTolerance/2 for ib in BinEdges if Toffset(run['lhcFill']['stableBeamsStart']) <= ib < Toffset(run['lhcFill']['stableBeamsEnd'])]:
                    if ibin not in X['SB']:
                        X['SB'].append(ibin)
                        Y['SB'].append(DETECTORS.index('STABLE BEAMS'))
        except:
            nodnwew =8
                
            
    fig, ax = plt.subplots(figsize=(20,4))

    for rtype in X:
        ax.hist2d(X[rtype],Y[rtype], bins=(BinEdges,[i for i in range(len(DETECTORS)+1)]), cmin=1, cmap=ColMaps[rtype] )
    ax.set_yticks(np.arange(len(DETECTORS)+1),labels=DETECTORS+['',],va='bottom')
    ax.grid(axis='y')

    legend_patches = []
    for rtype, cmap_name in ColMaps.items():
        if (rtype == 'unknown' and not foundUnknownRunType) or rtype == 'SB':
            continue
        patch_color = cmap_name(0)
        patch = mpatches.Patch(color=patch_color, label=rtype)
        legend_patches.append(patch)

    vlines = [24*i for i in range(9999) if 24*i <= BinEdges[-1]]
    for l in vlines:
        ax.axvline(l,linewidth=1,linestyle='-.', color='#7faceb')

    ax.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1, 0.5), title='Run type')
    
    ax.set_xlabel('time (h)')
    ax.xaxis.set_label_coords(1, -.05)
        

    if SavePng:
        plt.savefig('timetable.png', dpi=800)
    else:
        plt.show()


#______________________________________________________
def MDQUALITYTABLE(data,minduration):

    global DETECTORS
    DETECTORS.remove('STABLE BEAMS')
    qualitydict = {}  # qualitydict[run]=[good, bad, good ,,..., duration, fillnumber]
    noPhysicsRuns = []
    for run in data:
        runN = run['runNumber']
        ndet = run['nDetectors']
        if (ndet < 2):
            continue
        duration = round((int(run['runDuration'])/(1000*60)),1)
        if duration < minduration:
            continue
        try:
            if run['runType']['name'] in ['COSMICS','SYNTHETIC']:
                noPhysicsRuns.append(runN)
                continue
        except Exception as e:
            print('Exception in reading run type for run',runN,e)
            print('Exiting')
            sys.exit()
        qualitydict[runN] = list()
        qualities_det = [r['name'] for r in run['detectorsQualities']]
        qualities_qual = [r['quality'] for r in run['detectorsQualities']]
        detectors = run['detectors'].split(',')
        for det in DETECTORS:
            if det in detectors and det in qualities_det:
                qualitydict[runN].append(qualities_qual[qualities_det.index(det)])
            if det in detectors and det not in qualities_det:
                qualitydict[runN].append('?')
            if det not in detectors:
                qualitydict[runN].append('//')
        
        qualitydict[runN].append(duration)
        try:
            qualitydict[runN].append(run['lhcFill']['fillNumber'])
        except TypeError:
            qualitydict[runN].append(' ')

    header  = '| Run    |'
    for det in DETECTORS:
        header += (' ' + det.ljust(6) + ' |')
    header += ' Minutes | Fill   |'
    hline = '| ------ |'
    for det in DETECTORS:
        hline += ' ------ |'
    hline += ' ------- | ------ |'
    print(header)
    print(hline)
    for run in qualitydict:
        row = '| '+str(run)+' |'
        for j in qualitydict[run]:
            row += ' '+str(j).ljust(6)+' |'
        print(row)
    print('\n\nRuns in the table:',[r for r in qualitydict])
    print('\n\nThe followig runs are COSMICS or SYNTHETICs:',noPhysicsRuns)
        
#______________________________________________________
def EOR(data,SavePng):
    cosmicsdict = {}
    syntheticdict = {}
  
    for run in data:
        ndet = run['nDetectors']
        if (ndet < 2):
            continue
        try:
            eor = run['eorReasons'][0]['category']
        except IndexError:
            eor = 'None'
        if IsRunType(run,"TECHNICAL") or IsRunType(run,"SYNTHETIC"):
            continue
        
        if IsRunType(run,"COSMICS"):
            if eor in cosmicsdict:
                try:
                    cosmicsdict[eor].append([run['runNumber'], run['eorReasons'][0]['title'], run['eorReasons'][0]['description']])
                except:
                    cosmictdict[eos].append([run['runNumber'],'',''])
            else:
                try:
                    cosmicsdict[eor] = [[run['runNumber'], run['eorReasons'][0]['title'], run['eorReasons'][0]['description']],]
                except:
                    cosmicstdict[eos] = [[run['runNumber'],'',''],]
        else:
            if eor in syntheticdict:
                try:
                    syntheticdict[eor].append([run['runNumber'], run['eorReasons'][0]['title'], run['eorReasons'][0]['description']])
                except:
                    syntheticdict[eor].append([run['runNumber'],'',''])
            else:
                try:
                    syntheticdict[eor] = [[run['runNumber'], run['eorReasons'][0]['title'], run['eorReasons'][0]['description']],]
                except:
                    syntheticdict[eor] = [[run['runNumber'],'',''],]

    print('### EOR REASON STATISTICS')
    print(' --- COSMICS --- ')
    for eor in cosmicsdict:
        print(eor,':',len(cosmicsdict[eor]))
        if eor != 'Run Coordination':
            print('       ',cosmicsdict[eor])
    print(' --- NON COSMICS --- ')
    for eor in syntheticdict:
        print(eor,':',len(syntheticdict[eor]))
        print('       ',syntheticdict[eor])

    #DICT = cosmicsdict
    DICT = syntheticdict

    ListEOR = [eor for eor in DICT if eor != 'None']
    ListN = [len(DICT[eor]) for eor in DICT if eor != 'None']

    fig, ax = plt.subplots()
    palette = sns.color_palette('deep')
    palette[ListEOR.index('Run Coordination')] = (0.8,0.8,0.8)
    ax.pie(ListN, labels=ListEOR, colors=palette, startangle=80)
    

    if SavePng:
        plt.savefig('timetable.png', dpi=800)
    else:
        plt.show()
