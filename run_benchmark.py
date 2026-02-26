import os
from os import listdir
from os.path import isfile, join
import sys
import copy
import shutil
import FWCore.ParameterSet.Config as cms
import argparse
import json
import subprocess
from run_harvesting import run_harvesting

import timingserver.utils as utils
import timingserver.cmscfgutil as cmscfgutil

sys.path.insert(
    1, "{}/patatrack-scripts".format(os.path.dirname(os.path.abspath(__file__)))
)
from multirun import multiCmsRun, info, parseProcess

def convert_to_multirun_options(in_options):
    """
    returns a copy of the options object with variables not recognised by multiCmsRun removed
    """
    options = copy.deepcopy(in_options) 
    del options.data
    del options.input_sample
    del options.l1menu
    del options.confdb_address
    del options.global_tag
    del options.run_io_benchmark
    del options.config
    del options.cfg_args 
    del options.jobtype
    del options.no_l1_override
    del options.run_outputmods
    del options.only_make_config
    options.set_cpu_affinity = options.cpu_affinity
    options.set_gpu_affinity = options.gpu_affinity
    options.set_numa_affinity = options.numa_affinity
    del options.cpu_affinity
    del options.gpu_affinity
    del options.numa_affinity
    
    return options

def run_benchmark(options):
    if options.data == "None" and options.config is None:
        print(
            "Error! --data option was set to None and no config file was provided via the --config option! Exiting..."
        )
        sys.exit()

    if not os.path.exists(options.logdir):
        print("Directory provided in logdir option does not yet exist. Creating it...")
        os.makedirs(options.logdir)

    with open(options.logdir + "/commandline_args.txt", "w+") as f:
        json.dump(options.__dict__, f, indent=2)

    if options.config is None:
        utils.get_hlt_config(
            options.data, options.global_tag, options.confdb_address, options.logdir
        )
        options.config = join(options.logdir, "hlt.py")

   
    if options.keep is None:
        options.keep = ["DQMIO.root"]
    elif not "DQMIO.root" in options.keep:
        options.keep += ["DQMIO.root"]

    info()

    # now that all options were already parsed, we need to remove these from sys.argv,
    # otherwise we will get errors when parsing the process
    # TODO: This seems kind of fishy. Is there a more elegant way to do this?

    sys.argv = [sys.argv[0], options.config]

    if sys.argv[0].endswith(".py"):
        sys.argv[0] = sys.argv[0][:-3]

    process = parseProcess(options.config)

    cmscfgutil.cust_for_timing(process,options)

    cfg_custname = join(os.path.abspath(options.logdir), "hlt_customised.py")
    with open(cfg_custname,'w') as f:
        f.write(process.dumpPython())

    print(f"\nConfig file created at {cfg_custname}\nRun this cfg to debug job failures")
    if options.only_make_config:
        print("Config file created. Exiting...")
        sys.exit()

    run_io_benchmark = options.run_io_benchmark
    run_options = convert_to_multirun_options(options)

    if run_io_benchmark:
        # prepare a trimmed down configuration for benchmarking only reading the input data
        io_process = copy.deepcopy(process)
        io_process.hltGetRaw = cms.EDAnalyzer("HLTGetRaw", RawDataCollection = cms.InputTag("rawDataCollector"))
        io_process.path = cms.Path(io_process.hltGetRaw)
        io_process.schedule = cms.Schedule(io_process.path)
        if 'PrescaleService' in io_process.__dict__:
            del io_process.PrescaleService

        # benchmark reading the input data
        print('Benchmarking only I/O')
        io_options = dict(run_options.__dict__, logdir = None, keep = [])

        print("\n")
        print(io_process)
        print("-----")
        print(io_options)
        print("\n")
        
        multiCmsRun(io_process, **io_options)
        run_io_benchmark = False
        print()

    print("Begin running the full benchmark") #this line is looked for in the parser to get the throughput
    print("Benchmarking {}\n".format(options.config))
    multiCmsRun(process, **run_options.__dict__)


if __name__ == "__main__":
    if not "CMSSW_BASE" in os.environ:
        print(
            "ERROR! Your CMSSW environment has not been set up correctly.\n"
            "Please refer to the following twiki: "
            "https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookSetComputerNode"
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Config python file(s) to run the validation on.",
    )
    parser.add_argument(
        "--data",
        type=str,
        default="2018D",
        choices=["2018D", "MC2022", "2022", "2023", "2024","2025", "MCRun4Phase2Spring23", "Phase2Spring24","Phase2C17I13M9_ExtendedRun4D110"],
        help="Choose the data you want to run on. Choices are '2018D', 'MC2022', '2022', '2023', '2024', '2025', 'MCRun4Phase2Spring23' or 'Phase2Spring24'."
        " Choose 'None' if you have provided a custom hlt config"
        " that already specifies the data to run",
    )
    parser.add_argument(
        "--global-tag",
        dest="global_tag",
        type=str,
        default="auto:run2_hlt_relval",
        help='Choose global tag for your config. Default is "auto:run2_hlt_relval"'
        "This option is ignored if a config is provided.",
    )
    parser.add_argument(
        "--confdb-address",
        dest="confdb_address",
        type=str,
        default="/dev/CMSSW_11_3_0/GRun",
        help='Choose confdb address of the menu. Default is "/dev/CMSSW_11_3_0/GRun"'
        "This option is ignored if a config is provided.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Controls the verbosity of the program."
    )
    parser.add_argument("--plumbing", action="store_true", help="Unknown")
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="Conduct warmup job before doing the actual timing study.",
    )
    parser.add_argument(
        "--events", type=int, default=10100, help="Maximum number of events to run on."
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Set how often each job should be repeated.",
    )
    parser.add_argument("--jobs", type=int, default=1, help="Number of jobs.")
    parser.add_argument(
        "--threads", type=int, default=1, help="Number of threads per job."
    )
    parser.add_argument(
        "--streams", type=int, default=0, help="Number of EDM streams per job."
    )
    parser.add_argument(
        "--gpus-per-job",
        dest="gpus_per_job",
        type=int,
        default=1,
        help="Number of GPUs per job.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-n', '--numa-affinity',
                        dest = 'numa_affinity',
                        action = 'store_true',
                        default = False,
                        help = 'enable NUMA affinity [default: False]')
    group.add_argument('--no-numa-affinity',
                        dest = 'numa_affinity',
                        action = 'store_false',
                        help = 'disable NUMA affinity')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--cpu-affinity',
                        dest = 'cpu_affinity',
                        action = 'store_true',
                        default = True,
                        help = 'enable CPU affinity [default: True]')
    group.add_argument('--no-cpu-affinity',
                        dest = 'cpu_affinity',
                        action = 'store_false',
                        help = 'disable CPU affinity')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--gpu-affinity',
                        dest = 'gpu_affinity',
                        action = 'store_true',
                        default = True,
                        help = 'enable GPU affinity [default: True]')
    group.add_argument('--no-gpu-affinity',
                        dest = 'gpu_affinity',
                        action = 'store_false',
                        help = 'disable GPU affinity')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--run-io-benchmark',
                        dest = 'run_io_benchmark',
                        action= 'store_true',
                        default = True,
                        help = 'measure the I/O benchmarks before the other measurements [default: True]')
    group.add_argument('--no-run-io-benchmark',
                        dest = 'run_io_benchmark',
                        action= 'store_false',
                        help = 'skip the I/O measurement')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--allow-hyperthreading',
                        dest = 'allow_hyperthreading',
                        action = 'store_true',
                        default = True,
                        help = 'allow HyperThreading/Simultaneous multithreading (used only if cpu_affinity = True) [default: True]')
    group.add_argument('--no-hyperthreading',
                        dest = 'allow_hyperthreading',
                        action = 'store_false',
                        help = 'do not allow HyperThreading/Simultaneous multithreading (used only if cpu_affinity = True)')
    parser.add_argument(
        "--logdir",
        type=str,
        default="./timing_logs",
        help="Relative or absolute path where logfile should be saved. Default value is ./timing_logs",
    )
    parser.add_argument(
        "--keep",
        nargs="+",
        default=["DQMIO.root", "resources.json"],
        help="Additional output files to be kept, along with the logs.",
    )
    parser.add_argument(
        "--cfg-args",
        "-ca",
        dest="cfg_args",
        nargs="+",
        default=None,
        help="Additional arguments that should be passed to the custom HLT config file if specified in the --config option.",
    )
    parser.add_argument(
        "--input-sample",
        dest="input_sample",
        default="PU50",
        help="input pileup sample to run on"
    )
    parser.add_argument(
        "--l1menu",
        dest="l1menu",
        default="L1Menu_Collisions2018_v2_1_0_Col2",
        help="input l1 menu to run on"
    )
    #mild hack to transmit the job type, should only ever be timing
    parser.add_argument(
        "--jobtype",
        dest="jobtype",
        default="timing",
        help="job type"
    ) 
    parser.add_argument(
        "--no-l1-override",
        dest="no_l1_override",
        action="store_true",        
        help="stops the L1 override"
    )

    parser.add_argument(
        "--run-outputmods",
        dest="run_outputmods",
        action="store_true",
        help="runs the output modules"
    )
    parser.add_argument(
        "--only-make-config",
        dest="only_make_config",
        action="store_true",
        help="only makes the config file, does not run the benchmark"
    )

    options = parser.parse_args()
    

    
    print("Start running benchmark")
    run_benchmark(options)
    print("\n")

    #print(options)
    
    print("Now, running harvensting \n")
    run_harvesting(options)

    print("Done!")
