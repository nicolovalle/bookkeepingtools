import numpy as np
import pandas as pd
import requests
import json
import argparse
import re
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
#Daiki Sekihata
#daiki.sekihata@cern.ch
#Center for Nuclear Study, the University of Tokyo

parser = argparse.ArgumentParser('a script to download ALICE run info from https://ali-bookkeeping.cern.ch/api/runs');
parser.add_argument("-f", "--From", default="0", type=int, help="desired fill number from this value", required=True)
parser.add_argument("-t", "--To"  , default="99999" , type=int, help="desired fill number up to this value", required=True)
parser.add_argument("-s", "--Suffix"  , default="" , type=str, help="suffix for plots (e.g. week number etc)", required=False)
args = parser.parse_args();

#_____________________________________________________________________________________
def read_json(filename):
    json_open = open(filename, 'r');
    data = json.load(json_open);
    return data;
#_____________________________________________________________________________________
def plot_run_duration_per_det(df, suffix):
    list_det = [
        "CPV", "EMC", "FDD", "FT0", "FV0",
        "HMP", "ITS", "MCH", "MFT", "MID",
        "PHS", "TOF", "TPC", "TRD", "ZDC"
    ];
    ndet = len(list_det);
    lefts = np.arange(ndet)

    nrun = len(df);
    print("total number of run = ",nrun);

    list_duration_good_det = [0.0 for i in range(0,ndet)];
    list_duration_bad_det = [0.0 for i in range(0,ndet)];
    list_nrun_det = [0 for i in range(0,ndet)];

    for index, row in df.iterrows():
        timeh = float(row["runDuration"]) /3600./1e+3;#convert mili second to hour
        detname_1d = row["detectors"];

        if row["runQuality"] == "bad":
            continue;

        list_run_det = [j for j in detname_1d.split(',')];
        #print(list_run_det,len(list_run_det));

        for idet in range(0,len(list_run_det)):
            idx = list_det.index(list_run_det[idet]);
            list_duration_good_det[idx] += timeh;
            list_nrun_det[idx] += 1;

    mpl.rcParams['axes.xmargin'] = 0;
    fig = plt.figure(figsize=(12,9),dpi=100);
    plt.bar(lefts,list_duration_good_det,tick_label=list_det,align="center");
    plt.xticks(rotation=0,fontsize=20);
    plt.yticks(rotation=0,fontsize=20);
    plt.xlabel('detector', fontsize=20)
    plt.ylabel('running time (hour)', fontsize=20)
    plt.grid(axis='y');

    plt.subplots_adjust(left=0.08, right=0.99, top=0.99, bottom=0.08)
    date = datetime.date.today().strftime("%Y%m%d");
    plt.savefig("{0}_run_duration_per_det{1}.eps".format(date,suffix), format="eps",dpi=300);
    plt.savefig("{0}_run_duration_per_det{1}.pdf".format(date,suffix), format="pdf",dpi=300);
    plt.savefig("{0}_run_duration_per_det{1}.png".format(date,suffix), format="png",dpi=300);
    #plt.show()

#_____________________________________________________________________________________
def plot_run_duration(df, suffix):
    nrun = len(df);
    print("total number of run = ", nrun);
    df = df.iloc[::-1];

    list_fill_numbers = [];
    list_run_numbers = [];
    list_duration = [];
    list_color = [];
    for index, row in df.iterrows():
        list_fill_numbers.append(int(row['fillNumber']));
        list_run_numbers.append(int(row['runNumber']));
        list_duration.append(float(row['runDuration']) /3600./1e+3);#convert second to hour
        if row['runQuality'] == "good":
            list_color.append("green");
        elif row['runQuality'] == "bad":
            list_color.append("red");
        else:
            list_color.append("yellow");

    #print(list_fill_numbers);
    #print(list_run_numbers);
    #print(list_duration);
    y_max = 1.22 * max(list_duration);

    mpl.rcParams['axes.xmargin'] = 0;
    fig = plt.figure(figsize=(16,8),dpi=100);
    lefts = np.arange(len(list_run_numbers))
    plt.bar(lefts,list_duration,tick_label=list_run_numbers,align="center",color=list_color);
    plt.xticks(rotation=90,fontsize=15)
    plt.yticks(rotation=0,fontsize=18)
    plt.xlabel('run number', fontsize=18)
    plt.ylabel('run duration (hour)', fontsize=18)
    plt.ylim(0, y_max);
    plt.grid(axis='y');
    #plt.yticks([0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6.0])

    for j in range(0, nrun-1):
        if list_fill_numbers[j] != list_fill_numbers[j+1]:
            plt.vlines(j+0.5, 0, y_max, 'black', 'solid');
            plt.text(j-0.5, y_max*0.84, 'Fill {0}'.format(list_fill_numbers[j]), rotation=90, fontsize=18);
        if j == nrun-2:
            plt.vlines(j+1.5, 0, y_max, 'black', 'solid');
            plt.text(j+0.5, y_max*0.84, 'Fill {0}'.format(list_fill_numbers[j]), rotation=90, fontsize=18);
    plt.subplots_adjust(left=0.05, right=0.99, top=0.99, bottom=0.18)

    plt.plot([], [], marker="s", color="green", label="good", linestyle="none")
    plt.plot([], [], marker="s", color="red"  , label="bad", linestyle="none")
    #plt.plot([], [], marker="s", color="yellow"  , label="not tagged", linestyle="none")
    legend = plt.legend(frameon=False, handletextpad=1,fontsize=24)

    date = datetime.date.today().strftime("%Y%m%d");
    plt.savefig("{0}_run_duration{1}.eps".format(date,suffix), format="eps",dpi=300);
    plt.savefig("{0}_run_duration{1}.pdf".format(date,suffix), format="pdf",dpi=300);
    plt.savefig("{0}_run_duration{1}.png".format(date,suffix), format="png",dpi=300);
    #plt.show()

#_____________________________________________________________________________________
def plot_lhc_fill(df, suffix):
    #print(data);
    nrun = len(df);
    print("total number of good physics runs = ", nrun);
    df = df.iloc[::-1];

    list_filling_scheme_tmp = [];
    list_run_numbers = [];
    list_run_duration = [];
    list_fill_numbers = [];
    list_sb_duration = [];
    list_efficiency = [];
    for index, row in df.iterrows():
        list_sb_duration.append(float(row['lhcFill.stableBeamsDuration'])/3600.);
        list_fill_numbers.append(row['lhcFill.fillNumber']);
        list_filling_scheme_tmp.append(row['lhcFill.fillingSchemeName']);
        list_run_numbers.append(row['runNumber']);
        list_run_duration.append(float(row['runDuration'])/3600./1e+3);

    list_filling_scheme = [];
    list_sb_duration = sorted(set(list_sb_duration), key=list_sb_duration.index ); #remove duplicated fill numbers
    print("list_fill_numbers", list_fill_numbers);
    total_run = 0;
    list_total_run_duration = [];
    fill_number = list_fill_numbers[0];
    for j in range(0, nrun):
        if fill_number != list_fill_numbers[j] or j == nrun-1:
            fill_number = list_fill_numbers[j];
            list_total_run_duration.append(total_run);
            list_filling_scheme.append(list_filling_scheme_tmp[j]);
            total_run = 0;
        total_run += list_run_duration[j];
        #print('fill number = {0} , run number = {1}, total = {2}'.format(list_fill_numbers[j], list_run_numbers[j], total_run));

    for k in range(0, len(list_sb_duration)):
        run = list_total_run_duration[k];
        sb = list_sb_duration[k];
        list_efficiency.append(run/sb * 100);

    #print("list_total_run_duration", list_total_run_duration);
    #print("list_sb_duration", list_sb_duration);
    #print("list_efficiency", list_efficiency);

    list_fill_numbers = sorted(set(list_fill_numbers), key=list_fill_numbers.index ); #remove duplicated fill numbers
    #print(list_fill_numbers);

    mpl.rcParams['axes.xmargin'] = 0;
    fig = plt.figure(figsize=(18,8),dpi=100);
    gs = gridspec.GridSpec(2,1);#starting from top
    ax0 = plt.subplot(gs[0]);
    ax1 = plt.subplot(gs[1],sharex=ax0);

    #bottom_tmp = np.array(list_t1st,dtype=float) + np.array(list_total_run_duration,dtype=float);
    bottom_tmp = 0;
    lefts = np.arange(len(list_fill_numbers))

    ax0.plot(lefts, list_efficiency ,label="",marker="o");
    ax1.bar(lefts,list_sb_duration     , tick_label=list_fill_numbers, align="edge", width=-0.4, label="stable beam duration", color='blue');
    ax1.bar(lefts,list_total_run_duration, tick_label=list_fill_numbers, align="edge", width=+0.4, label="ALICE running time", color='green');

    ax1.set_xlabel('fill number', fontsize=20)
    ax0.set_ylabel('efficiency (%)', fontsize=20)
    ax1.set_ylabel('duration (hour)', fontsize=20)

    ax0.set_yticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    ax0.set_ylim([-5,100]);
    #ax1.set_yticks([0,10,20,30,40,50])
    #ax1.set_yticks([0,2,4,6,8,10,12,14])
    ax1.set_ylim([0,max(list_sb_duration)+2]);

    ax0.grid(axis='both');
    ax1.grid(axis='both');

    ax1.legend(title="pp at $\sqrt{s}$ = 13.6 TeV", fontsize=18,title_fontsize=18);
    ax0.tick_params(labelsize=18);
    ax1.tick_params(labelsize=18);

    plt.subplots_adjust(hspace=.0)
    plt.subplots_adjust(left=0.06, right=0.99, top=0.98, bottom=0.14)

    #for i in range(0, len(list_sb_duration)):
    #    ax1.text(i-0.25, 1, '{0}'.format(list_filling_scheme[i].replace("b_","b_\n").replace("bpi_", "bpi_\n")), rotation=90, fontsize=18);

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.xticks(rotation=90,fontsize=18)

    date = datetime.date.today().strftime("%Y%m%d");
    plt.savefig("{0}_LHC_fill_data{1}.eps".format(date,suffix), format="eps",dpi=300);
    plt.savefig("{0}_LHC_fill_data{1}.pdf".format(date,suffix), format="pdf",dpi=300);
    plt.savefig("{0}_LHC_fill_data{1}.png".format(date,suffix), format="png",dpi=300);
    #plt.show();

#_____________________________________________________________________________________
if __name__ == "__main__":
    fillNumbers_int = list(range(args.From, args.To+1, 1));
    fillNumbers_str = [str(n) for n in fillNumbers_int];
    fillNumbers_str_comma = ','.join(fillNumbers_str);
    print(fillNumbers_str_comma);
    #fillter[fillNumbers] allows comma separated fill numbers.
    req = requests.get('https://ali-bookkeeping.cern.ch/api/runs?filter[fillNumbers]={0}&page[offset]=0&page[limit]=999'.format(fillNumbers_str_comma),verify=False)
    data = json.loads(req.text)['data'];
    filename = 'ALICE_run_data_fill_{0}_{1}.json'.format(args.From, args.To);
    with open (filename, 'w') as f:
        json.dump(data, f, indent=2);
    exit()
    data = read_json(filename);
    df = pd.json_normalize(data);
    df_physics = df[ (df['definition'] == "PHYSICS") & (df['runType.name']=="PHYSICS") & (df['lhcBeamMode']=="STABLE BEAMS") ];

    print("n physics run = ", len(df_physics));

    suffix = args.Suffix;
    plot_run_duration(df_physics, suffix);
    plot_run_duration_per_det(df_physics, suffix);
    df_physics_good = df[ (df['definition'] == "PHYSICS") & (df['runType.name']=="PHYSICS") & (df['lhcBeamMode']=="STABLE BEAMS") & (df['runQuality']=="good")];
    plot_lhc_fill(df_physics_good, suffix);

