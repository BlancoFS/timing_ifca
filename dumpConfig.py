import shutil
import subprocess

#input_cfg = "TimingConfiguration/HLTPhase2_timing_default_cff.py"
input_cfg = "TimingConfiguration/HLTPhase2_timing_seedless_cff.py"

cfg_tmpname = "timing_server_cmssw_cfg_tmp.py"
cfg_name = "timing_server_cmssw_cfg.py"

shutil.copyfile(input_cfg, cfg_tmpname)
with open(cfg_tmpname,'a') as f:
    f.write("\nfrom Configuration.AlCa.GlobalTag import GlobalTag as customiseGlobalTag")
    f.write(f"\nprocess.GlobalTag = customiseGlobalTag(process.GlobalTag, globaltag = '150X_mcRun4_realistic_v1')")
    f.write(f"\nopen('{cfg_name}', 'w').write(process.dumpPython())\n")

dump_cmd = f"python3 {cfg_tmpname}"
proc = subprocess.Popen(dump_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out_py3,err_py3 = proc.communicate()
