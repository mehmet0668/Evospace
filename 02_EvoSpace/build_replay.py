#!/usr/bin/env python3
"""Build the archived EvoSpace replay targets against the existing Mate ARGoS runtime.

This builds inference/replay only. It does not build or execute the optimizer.
The original C++ files are not edited.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-runtime', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cxx', default='g++')
    args = parser.parse_args()
    bundle = Path(__file__).resolve().parent
    source = bundle / 'source'
    base = json.loads(args.base_runtime.read_text())
    prefix = Path(base['prefix'])
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    common = [args.cxx, '-std=gnu++11', '-Os', '-DNDEBUG',
              '-DARGOS_simulator_BUILD', '-fPIC', '-I' + str(prefix / 'include'),
              '-I' + str(source), '-L' + str(prefix / 'lib/argos3'),
              '-Wl,-rpath,' + str(prefix / 'lib/argos3'), '-L' + str(out),
              '-Wl,-rpath,' + str(out), '-Wl,--allow-shlib-undefined']
    commands = [
        common + ['-shared', *map(str, (source / 'src/NEAT').glob('*.cpp')),
                  '-o', str(out / 'libneat.so')],
        common + ['-shared', str(source / 'src/NEATController.cpp'), '-lneat',
                  '-largos3plugin_simulator_epuck', '-o', str(out / 'libneat_controller.so')],
        common + ['-shared', str(source / 'src/controllers/NeuralNetworkRM3Dot1.cpp'),
                  '-lneat_controller', '-largos3core_simulator',
                  '-largos3plugin_simulator_epuck', '-largos3plugin_simulator_genericrobot',
                  '-largos3_demiurge_epuck_dao', '-o', str(out / 'libnn_rm_3Dot1.so')],
        common + [str(source / 'src/program/launch.cpp'), '-lneat', '-lneat_controller',
                  '-largos3core_simulator', '-largos3plugin_simulator_epuck',
                  '-Wl,--no-as-needed', '-Wl,--no-as-needed', '-largos3_demiurge_loop_functions', '-largos3_demiurge_epuck_dao', '-largos3plugin_simulator_epuck', '-largos3plugin_simulator_genericrobot', '-largos3core_simulator', '-largos3plugin_simulator_epuck',
                  '-o', str(out / 'NEAT-launch')],
    ]
    for index, command in enumerate(commands):
        completed = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        (out / f'build_{index}.log').write_text(completed.stdout)
        if completed.returncode:
            raise RuntimeError(f'Build target {index} failed; see its log.')
    runtime = {
        'source_semantics_edits': [], 'optimizer_built': False,
        'base_runtime': str(args.base_runtime.resolve()),
        'base_runtime_sha256': digest(args.base_runtime),
        'prefix': base['prefix'], 'plugin_dir': base['plugin_dir'],
        'metrics': base['metrics'], 'binary': str(out / 'NEAT-launch'),
        'library': str(out / 'libnn_rm_3Dot1.so'), 'build_dir': str(out),
        'commands': commands,
        'binary_sha256': {name: digest(out / name) for name in
                          ['NEAT-launch', 'libneat.so', 'libneat_controller.so', 'libnn_rm_3Dot1.so']},
    }
    (out / 'runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')
    print(out / 'runtime.json')


if __name__ == '__main__':
    main()
