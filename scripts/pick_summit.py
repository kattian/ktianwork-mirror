#!/usr/bin/env python


import logging

import sys
import os
import argparse

logging.basicConfig(
        format='%(asctime)s %(levelname)-5s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

logging.info(" ".join(sys.argv))



"""
TFNET_ROOT is set to the root of TFNET dir
 +-- scripts       such as label_region, prepare_data.py, run_deeplift.py, run_modisco.py, run_pipeline.py etc
 +-- genome        hg19.fa hg19.chrom.sizes
 +-- ENCODE_data   intervals
 +-- results       results of the pipeline
      +-- ZNF143
      +-- CTCF
      +-- SIX5
"""
ROOT_DIR   = os.getenv('TFNET_ROOT', "../../") 
scriptDir  = ROOT_DIR + "/scripts/"
dataDir    = ROOT_DIR + "/ENCODE_data/"
genomeDir  = ROOT_DIR + "/genome/"
resultsDir = "./"
logDir     = resultsDir + "log/"
#tmpDir     = "./tmp/"

# must run from resultsDir

# loop through the TFs
#for tf in ['ZNF143']:

import gzip
def process_files(in_names, bin_size):
    for in_name in in_names:
        with gzip.open(in_name,'r') as tsvin:

            for cnt, line in enumerate(tsvin):
            
                fields = line.split('\t')
                if len(fields) < 10:
                    continue

                chrom = fields[0]
                start = int(fields[1])
                end   = int(fields[2])
                peak  = int(fields[9])
                left  = start + peak - int(bin_size/2)

                sys.stdout.write(chrom + "\t" + str(left) + "\t" + str(left + bin_size) + "\n")
    
        
def process_tf(tfs, cell_set=None, expr=None):

            #           -4   -3    -2          -1
    #neutrophil-CTCF-human-ENCSR785YRL-optimal_idr.narrowPeak.gz
    #neutrophil-CTCF-human-ENCSR785YRL-rep1.narrowPeak.gz
    #neutrophil-CTCF-human-ENCSR785YRL-rep2.narrowPeak.gz

    if expr == None:
        expr_str = ""
    else:
        expr_str = expr

    import glob
    tf_files = []
    for tf in tfs:
        tf_files.extend(glob.glob(dataDir + "*-" + tf + "-human-" + expr_str + "*-optimal*"))

    count = 0
    task_list = []
    for path_name in tf_files:
        fn = os.path.basename(path_name)
        fn_list = fn.split('-')
        exp  = fn_list[-2]
        tf   = fn_list[-4]
        cell = '-'.join(fn_list[:-4])
        if cell_set != None and len(cell_set) != 0: # select cells only in the specified set
            if not cell in cell_set:
                continue
        task_list.append([cell, tf, exp])
        sys.stderr.write(path_name + "\n")
        count = count + 1

    #print(task_list)
    #print(count)

    positives = []
    for cell, tf, exp in task_list:

        positive = dataDir + cell + "-" + tf + "-human-" + exp + "-optimal_idr.narrowPeak.gz"
        if not os.path.isfile(positive):
            continue
            #print("ERR does not exist: ", positive)
        positives.append(positive)

    process_files(positives, 1000)


# guarantee to clean up tmp dir
import contextlib
import tempfile
import shutil
@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp(dir = ".", prefix = "_tmp_")
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def parse_args(args = None):
    parser = argparse.ArgumentParser('run_pipeline.py',
                                     description='run pipe line for TF binding training',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--tfs', type=str, help="List of transcription factors, separated by ','")
    parser.add_argument('--cells', type=str, default=None, help="List of cell-lines, separated by ','")
    parser.add_argument('--expr', type=str, default=None, help="Experiment Id")
    parser.add_argument('--data-dir', type=str, default=None, help="DataDir")
    args = parser.parse_args(args)
    return args

if __name__ == '__main__':

    args = parse_args()
    tfs = args.tfs
    cell_lines = args.cells
    if args.data_dir != None:
        dataDir = args.data_dir + "/"
        sys.stderr.write("dataDir=" + dataDir + ", tfs=" + tfs + ", cells=" + str(cell_lines) + "\n")

    with make_temp_directory() as temp_dir:
        global tmpDir
        tmpDir = temp_dir + "/"

        tfs = tfs.split(',')
        if cell_lines == '-' or cell_lines == None:
            cell_set = None
        else:
            cell_lines = cell_lines.split(',')
            cell_set = set(cell_lines)
        process_tf(tfs, cell_set, args.expr)

