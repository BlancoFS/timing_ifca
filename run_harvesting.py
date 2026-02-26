import os
import pathlib
import shutil
import glob
import subprocess

import timingserver.utils as utils

def get_input_files_str(files,options):
    if options.jobtype=="timing": #only take one job for timing
        return files[0]
    else: #for validation take all
        return ",".join(files)


def run_harvesting_worker(cfg_name,input_files,logdir,logfilename,outtag):
    print("running harvesting")
    cfg_file_full_path = os.path.join(
            #we are in the scripts dir so need to go up one to get the cmss
            pathlib.Path(os.path.abspath(__file__)).parent.parent,"cmssw_cfgs",cfg_name
        )

    with subprocess.Popen(
        [
            "cmsRun",
            cfg_file_full_path,
            f"inputFiles={','.join(input_files)}",
            f"outTag={outtag}",
            "filePrepend=file:"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=logdir) as process:
        try:
            out, err = process.communicate(timeout=400.)
            with open(os.path.join(os.path.abspath(logdir), logfilename), "w") as f:
                f.write(out)
                f.write(err)
        except subprocess.TimeoutExpired:
            print("harvesting job timed out")
            process.kill()
            out, err = process.communicate()
            with open(os.path.join(os.path.abspath(logdir), logfilename), "w") as f:
                f.write(out)
                f.write(err)



def run_harvesting(options):
    repeats = options.repeats if hasattr(options,"repeats") else 1
    
    for repeatnr in range(0,repeats):

        logdir = options.logdir + "/logs/step%04d" % (repeatnr)    
        dqm_files = glob.glob(os.path.join(logdir,"*","*DQMIO*.root"))            
        cfg  = "harvesting.py" if options.jobtype=="timing" else "harvesting_val.py"
        logfilename = f"harvesting_repeat{repeatnr}.log"

        print(" ----- run_harvesting_worker ----- ")
        print(f"cfg         -> {cfg}")
        print(f"dqm_files   -> {dqm_files}")
        print(f"logdir      -> {logdir}")
        print(f"logfilename -> {logfilename}")
        print(f"Repeat      -> {repeatnr}")
        
        run_harvesting_worker(cfg,[dqm_files[0]],logdir,logfilename,f"Repeat{repeatnr}")

    # remove pycache
    if os.path.exists(os.path.abspath(options.logdir) + "/__pycache__"):
        shutil.rmtree(os.path.abspath(options.logdir) + "/__pycache__")

    
