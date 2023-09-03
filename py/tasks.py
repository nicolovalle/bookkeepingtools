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
from matplotlib import gridspec
from datetime import datetime
from datetime import date
import seaborn as sns


utctosec = 1./(1000)
utctoh = 1./(1000*60*60)
DETECTORS = ["CPV", "EMC", "FDD", "FT0", "FV0", "HMP", "ITS", "MCH", "MFT", "MID", "PHS", "TOF", "TPC", "TRD", "ZDC"]
#DETECTORS.reverse()

firsttimestamp = datetime.now()
firstmidnight = datetime.now()


def Toffset(ut):
    return (datetime.fromtimestamp(ut*utctosec) - firstmidnight).total_seconds()/3600


#______
def IsCosmics(run):
    return run['runType']['name']=="COSMICS"

#___________________________________________________________
def TIMETABLE(data,SavePng):

    global firsttimestamp
    global firstmidnight
    
    utc0 = data[0]['startTime']
    print('AAAAAAA',utc0)
    firsttimestamp = datetime.fromtimestamp(utc0*utctosec)
    firstmidnight = firsttimestamp.replace(hour=0,minute=0,second=0)
    print(firstmidnight)
    X=[]
    Y=[]
    BinEdges = []
    for run in data:
        ndet = run['nDetectors']
        if (ndet < 2):
            continue
        BinEdges.append(Toffset(run['startTime']))
        BinEdges.append(Toffset(run['endTime']))
    print(BinEdges)
    for run in data:
        ndet = run['nDetectors']
        if (ndet < 2):
            continue
        list_det = run['detectors'].split(',')
        list_det_id = [DETECTORS.index(idet) for idet in list_det]
        #print('RUN')
        #print(list_det_id)
        start_bin = Toffset(run['startTime']+1)
        for idet in list_det_id:
            X.append(start_bin)
            Y.append(idet)
            if IsCosmics(run):
                X.append(start_bin)
                Y.append(idet)

    fig, ax = plt.subplots(figsize=(20,4))
    ax.hist2d(X,Y, bins=(BinEdges,[i for i in range(len(DETECTORS)+1)]), cmin=1)
    ax.set_yticks(np.arange(len(DETECTORS)+1),labels=DETECTORS+['',],va='bottom')
    ax.grid(axis='y')

    vlines = [24*i for i in range(9999) if 24*i <= BinEdges[-1]]
    for l in vlines:
        ax.axvline(l,linewidth=1,linestyle='-.', color='#7faceb')
        
    ax.set_xlabel('time (h)')
    ax.xaxis.set_label_coords(1, -.05)
        

    if SavePng:
        plt.savefig('timetable.png', dpi=800)
    else:
        plt.show()


#______________________________________________________
def MDQUALITYTABLE(data,minduration):

    qualitydict = {}  # qualitydict[run]=[good, bad, good ,,..., duration, fillnumber] 
    for run in data:
        runN = run['runNumber']
        ndet = run['nDetectors']
        if (ndet < 2):
            continue
        duration = round((int(run['runDuration'])/(1000*60)),1)
        if duration < minduration:
            continue
        qualitydict[runN] = list()
        qualities_det = [jj['name'] for jj in run['detectorsQualities']]
        qualities_qual = [jj['quality'] for jj in run['detectorsQualities']]
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
        if IsCosmics(run):
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
    print(' --- SYNTHETICS --- ')
    for eor in syntheticdict:
        print(eor,':',len(syntheticdict[eor]))
        if eor != 'Run Coordination':
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
