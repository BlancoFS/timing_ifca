# timing_ifca
This repository contains the instructions and scripts to run CMSSW HLT timing studies at the IFCA's HEP GPU cluster in Altamira.  

## Start GPU interactive job

```bash
srun --partition wncmsgpu --pty -N 1 -n 1 -c 42 /bin/bash
```

## First time you use it

```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsrel CMSSW_16_0_0_pre4
cd CMSSW_16_0_0_pre4/src

git clone https://github.com/BlancoFS/timing_ifca.git
git clone --recursive https://gitlab.cern.ch/cms-tsg/steam/timing.git

cp timing_ifca/run_benchmark.py timing/timingserver/scripts/
cp timing_ifca/run_harvesting.py timing/timingserver/scripts/
cp timing_ifca/multirun.py timing/patatrack-scripts/
cp timing_ifca/dumpConfig.py ./
cp timing_ifca/runTiming.sh ./
cp timing_ifca/L1Menu_Phase2_1500_Phase2Spring24_DYMM-PU200.list ../../SingleIterLuca/CMSSW_16_0_0_pre4/src/timing/timingserver/input_filelists/srv-b1b07-16-01/
cp timing_ifca/srv-b1b07-16-01.json ../../SingleIterLuca/CMSSW_16_0_0_pre4/src/timing/timingserver/cfgs/
```

## Activate environment

Mainly, doing `cmsenv` 

```bash
source activate.sh
```

## Dump HLT configuration

Get your desired HLT configuration file as:

```bash
cmsDriver.py Phase2 -s L1P2GT,HLT:75e33_timing --processName=HLTX \
--conditions auto:phase2_realistic_T33 \
--geometry ExtendedRun4D110 \
--era Phase2C17I13M9 \
--eventcontent FEVTDEBUGHLT \
--customise SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000 \
--filein file:dummy.root \
--inputCommands='keep *, drop *_hlt*_*_HLT, drop triggerTriggerFilterObjectWithRefs_l1t*_*_HLT' \
--python_filename HLTPhase2_timing.py \
--mc \
-n -1 --nThreads 1 --no_exec --output={}
```

In the step above, or editing the `HLTPhase2_timing.py` file, you can easily add a customizer to test your desired scenario for the phase-2 trigger menu. For example, adding the lines:

```python
from customizerForPhase2L3MuonFromGeneralTracks import *
process = customizerForPhase2L3MuonFromGeneralTracks(process, False, "MYHLT", False)
```

Then, dump the whole configuration:

```bash
edmConfigDump HLTPhase2_timing.py > HLTPhase2_timing_cff.py
```

Open this script to introduce the path to your HLT configuration. Now, run to adapt it for the timing measurements:

```bash
python3 dumpConfig.py
```

## Run timing measurements

The final results should be placed under the `outputs/logs` folder. The `resources.json` file contains all the encessary information to create the pie charts. 

```bash
./runTiming.sh
```

## Pie charts (circles)

To create a web page with ouyr results using circles, clone this repository:

```bash
git clone https://github.com/fwyzard/circles
```

Copy the content of `circles/web` to a webpage space. For example, in lxplus:

```bash
cp -r circles/web/* /eos/user/u/username/www/MyResultsFolder/
```

If running at IFCA:

```bash
scp output/logs/resources.json username@lxplus.cern.ch:/eos/user/u/username/www/MyResultsFolder/data/
```