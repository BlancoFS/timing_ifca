#!/bin/bash 

source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsenv
ulimit -Ss unlimited
export PYTHON3PATH=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/timing:$PYTHON3PATH
export PYTHON3PATH=/gpfs/users/blancose/TSGTiming/CMSSW_16_0_0_pre4/src/timing/patatrack-scripts:$PYTHON3PATH
source venv/bin/activate
