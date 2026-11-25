#!/usr/bin/env python3
"""Build optional CC observer and explicit ground-memory initialization diagnostic.

Usage:
  python build_cc_diagnostics.py --runtime /path/runtime.json --out /path/diagnostics

Keep observe_cc_v2.cpp beside this script. Requires the frozen runtime's source
directories and installed ARGoS/e-puck headers. Does not install or modify any
part of that runtime. The ground variant changes controller semantics and must
be reported as a diagnostic repair, not as untouched historical reproduction.
"""
import argparse,datetime,difflib,hashlib,json,pathlib,shutil,subprocess

EXPECTED_SOURCE_SHA256='aba71142cc32092d91d55ab5ad484c2c8c4d48ef8a30d8270e84c217bf34ff99'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def run(argv,log):
    p=subprocess.run(argv,capture_output=True,text=True)
    log.write_text(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(f'Build failed ({p.returncode}); inspect {log}')
def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--runtime',type=pathlib.Path,required=True)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    ap.add_argument('--cxx',default='g++')
    a=ap.parse_args();runtime_path=a.runtime.resolve();out=a.out.resolve()
    r=json.loads(runtime_path.read_text());prefix=pathlib.Path(r['prefix']);dao=pathlib.Path(r['source_dirs']['dao'])/'src';metrics=pathlib.Path(r['source_dirs']['metrics']);plugins=pathlib.Path(r['plugin_dir'])
    protected=[prefix.resolve(),*[pathlib.Path(p).resolve() for p in r['source_dirs'].values()]]
    if any(out==p or p in out.parents for p in protected):
        raise ValueError('--out must be outside all frozen runtime source/prefix directories')
    original=dao/'ReferenceModel3Dot1.cpp'
    if sha(original)!=EXPECTED_SOURCE_SHA256:
        raise ValueError('Unexpected ReferenceModel3Dot1.cpp. This diagnostic is audited for DAO89f605c; inspect another source version before applying.')
    observer_source=pathlib.Path(__file__).resolve().parent/'observe_cc_v2.cpp'
    if not observer_source.exists():raise FileNotFoundError('Keep observe_cc_v2.cpp beside this builder')
    out.mkdir(parents=True,exist_ok=True)
    copied=out/'dao_source';shutil.copytree(dao,copied,dirs_exist_ok=True)
    target=copied/'ReferenceModel3Dot1.cpp';old=target.read_text()
    needle='  m_deqGroundInput.push_back(s_ground_input);\n'
    if old.count(needle)!=1:raise ValueError('Unexpected SetGroundInput implementation')
    replacement='''  // Diagnostic warm start: populate the five-sample history using the first
  // actual sensor observation. No random draws or sensor/dynamics changes.
  // This intentionally changes initialization semantics; not a paper replay.
  if (m_deqGroundInput.empty()) {
    for (unsigned i = 0; i < 5; ++i) m_deqGroundInput.push_back(s_ground_input);
  } else {
    m_deqGroundInput.push_back(s_ground_input);
  }
'''
    new=old.replace(needle,replacement);target.write_text(new)
    patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original/ReferenceModel3Dot1.cpp',tofile='ground_warmstart/ReferenceModel3Dot1.cpp'))
    (out/'ground_warmstart.patch').write_text(patch)
    libdir=out/'ground_warmstart_library';libdir.mkdir(exist_ok=True)
    daolib=libdir/'libargos3_demiurge_epuck_dao.so'
    flags=[a.cxx,'-std=gnu++11','-Os','-DNDEBUG','-fPIC','-shared','-DARGOS_simulator_BUILD']
    cmd=flags+['-I'+str(prefix/'include'),'-I'+str(copied)]+[str(copied/x) for x in ['EpuckDAO.cpp','RabMessageBuffer.cpp','ReferenceModel1Dot1.cpp','ReferenceModel1Dot2.cpp','ReferenceModel3Dot1.cpp']]+['-L'+str(plugins),'-Wl,-rpath,'+str(plugins),'-Wl,--no-as-needed','-Wl,-soname,libargos3_demiurge_epuck_dao.so','-largos3plugin_simulator_epuck','-largos3core_simulator','-o',str(daolib)]
    run(cmd,out/'ground_warmstart_build.log')
    obsdir=out/'observer';obsdir.mkdir(exist_ok=True)
    obs=obsdir/'observe_cc_v2.cpp';shutil.copy2(observer_source,obs)
    obslib=obsdir/'libobserved_mate_cc.so';metriclib=pathlib.Path(r['metrics']['cc']).parent
    obscmd=flags+['-I'+str(prefix/'include'),'-I'+str(metrics),str(obs),'-L'+str(metriclib),'-L'+str(plugins),'-Wl,-rpath,'+str(metriclib)+':'+str(plugins),'-Wl,--no-as-needed','-lmate_cc_loopfunc','-largos3_demiurge_loop_functions','-largos3plugin_simulator_epuck','-largos3core_simulator','-o',str(obslib)]
    run(obscmd,out/'observer_build.log')
    changed=[]
    for p in dao.rglob('*'):
        if p.is_file() and sha(p)!=sha(copied/p.relative_to(dao)):changed.append(str(p.relative_to(dao)))
    assert changed==['ReferenceModel3Dot1.cpp'],changed
    manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'diagnostic_only':True,'runtime_manifest':str(runtime_path),'runtime_manifest_sha256':sha(runtime_path),'frozen_runtime_modified':False,'changed_source_files':changed,'original_rm31_sha256':sha(original),'diagnostic_rm31_sha256':sha(target),'patch_sha256':sha(out/'ground_warmstart.patch'),'ground_library':str(daolib),'ground_library_sha256':sha(daolib),'ground_build_command':cmd,'observer_library':str(obslib),'observer_library_sha256':sha(obslib),'observer_source_sha256':sha(obs),'observer_build_command':obscmd,'observer_label':'observed_mate_cc','observer_behavior':'Calls original scorer unchanged; no RNG draws; logs all20poses at0,1..10,100..1200andpostexperiment; counts1200PostSteps.','application':'Set LD_PRELOAD to ground_library for a single explicitly labeled run. To observeCC, change only loop_functions library to observer_library and label to observed_mate_cc. Leave params unchanged. Output is written into processcwd.','limitation':'OnlyRM3.1 is modified. This affects any FSM executed using the Mate/RM3.1controller, including Chocolate-FSM diagnostic transfers; it does not repair or reproduce originalChocolateRM1.1/RM1.2.'}
    (out/'build_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:manifest[k] for k in ['ground_library','observer_library','changed_source_files','diagnostic_only']},indent=2))
if __name__=='__main__':main()
