#!/bin/sh                                                                                                                                                                                                                                                                       
cd /gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src
source /cvmfs/cms.cern.ch/cmsset_default.sh

cmsenv

echo "Sourcing and starting!"

export PYTHON3PATH=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/timing:$PYTHON3PATH
export PYTHON3PATH=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/timing/patatrack-scripts:$PYTHON3PATH

echo "Set nvidia MPS seetings to /tmp/nvidia_mps"

export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia_mps
export CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia_mps

nvidia-cuda-mps-control -d

export CUDA_VISIBLE_DEVICES=0,1

######
export TIMINGSERVER_PKGPATH=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/timing
export TIMINGSERVER_BASE_WORKING_DIR=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/
export TIMINGSERVER_INPUTFILE_DIR=/gpfs/projects/cms/sblancof/
export TIMINGSERVER_SERVER_CFG=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/timing/timingserver/cfgs/srv-b1b07-16-01.json
# export TIMINGSERVER_CI_SECRET = 
export TIMINGSERVER_MPS_PIPE_DIRECTORY=/tmp/nvidia_mps
export TIMINGSERVER_MPS_LOG_DIRECTORY=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/output/Logs

echo "Final cmsRun"

python3 /gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/timing/timingserver/scripts/run_benchmark.py --config timing_server_cmssw_cfg.py --data Phase2C17I13M9_ExtendedRun4D110 --events 2000 --jobs 8 --threads 8 --streams 8 --logdir /gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/output --l1menu L1Menu_Phase2_1500 --input-sample DYMM-PU200  --repeats 3 --cpu-affinity --no-numa-affinity --gpu-affinity --run-io-benchmark --allow-hyperthreading
