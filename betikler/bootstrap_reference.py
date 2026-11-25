#!/usr/bin/env python3
"""Build pinned reference simulators entirely inside a user-owned runtime directory.

Python 3 standard library only. No downloads, package installations, sudo or system edits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import time
import zipfile


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def inside(root: Path, path: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def extract_zip(archive: Path, destination: Path) -> None:
    """Unlike ZipFile.extractall, preserve Unix symlinks and executable modes."""
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            rel = PurePosixPath(item.filename)
            if rel.is_absolute() or '..' in rel.parts:
                raise ValueError(f'Unsafe archive path: {item.filename}')
            target = destination.joinpath(*rel.parts)
            if not inside(destination, target):
                raise ValueError(f'Archive path escapes destination: {item.filename}')
            mode = item.external_attr >> 16
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(item)
            if stat.S_ISLNK(mode):
                link = data.decode('utf-8')
                if Path(link).is_absolute() or not inside(destination, target.parent / link):
                    raise ValueError(f'Unsafe archive symlink: {item.filename} -> {link}')
                if target.is_symlink():
                    if os.readlink(target) != link:
                        raise ValueError(f'Existing symlink differs: {target}')
                elif target.exists():
                    raise ValueError(f'Existing file blocks symlink: {target}')
                else:
                    target.symlink_to(link)
            else:
                target.write_bytes(data)
                if mode & 0o777:
                    target.chmod(mode & 0o777)


def patch_exact(path: Path, old: str, new: str, reason: str, records: list) -> None:
    before = path.read_text()
    before_sha = sha256(path)
    if new in before:
        records.append({'path': str(path), 'reason': reason, 'already_applied': True, 'sha256': before_sha})
        return
    if before.count(old) != 1:
        raise ValueError(f'Expected one exact patch anchor in {path}; found {before.count(old)}')
    path.write_text(before.replace(old, new, 1))
    records.append({'path': str(path), 'reason': reason, 'before_sha256': before_sha, 'after_sha256': sha256(path), 'old': old, 'new': new})


def main() -> int:
    package = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path, default=package / 'runtime')
    parser.add_argument('--cmake', default=shutil.which('cmake'), help='CMake 3.x executable; tested with 3.27.9.')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--extract-only', action='store_true')
    args = parser.parse_args()
    runtime = args.runtime_dir.resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    logs = runtime / 'logs'
    logs.mkdir(exist_ok=True)
    source_manifest = json.loads((package / 'sources/manifest.json').read_text())
    entries = {x['id']: x for x in source_manifest['sources']}
    extracted = {}
    archive_checks = []
    for key, entry in entries.items():
        archive = package / 'sources' / entry['filename']
        observed = sha256(archive)
        if observed != entry['sha256']:
            raise ValueError(f'Archive SHA-256 mismatch: {archive}')
        archive_checks.append({'id': key, 'archive': str(archive), 'sha256': observed, 'verified': True})
        if archive.suffix != '.zip':
            continue
        target = runtime / 'source' / key
        marker = target / '.archive_sha256'
        if marker.exists():
            if marker.read_text().strip() != observed:
                raise ValueError(f'Runtime source belongs to a different archive: {target}')
        else:
            extract_zip(archive, target)
            marker.write_text(observed + '\n')
        extracted[key] = target / entry['archive_root']
    write_json(logs / 'archive_checks.json', archive_checks)

    patch_records = []
    patch_exact(extracted['epuck'] / 'src/CMakeLists.txt',
                'include_directories(${CMAKE_SOURCE_DIR} ${ARGOS_INCLUDE_DIRS})',
                'include_directories(BEFORE ${CMAKE_SOURCE_DIR})\ninclude_directories(${ARGOS_INCLUDE_DIRS})',
                'Prefer extended e-puck headers over stock e-puck headers already installed with the core simulator.', patch_records)
    patch_exact(extracted['epuck'] / 'src/plugins/robots/e-puck/CMakeLists.txt',
                '  include(VisionTools.cmake)',
                '  if(QT_FOUND)\n    include(VisionTools.cmake)\n  endif()',
                'Build optional camera GUI utilities only when Qt is present; simulator camera and robot physics remain enabled.', patch_records)
    patch_exact(extracted['metrics'] / 'loop-functions/CMakeLists.txt',
                'add_subdirectory(gianduja)',
                '# Reference kit: unrelated Gianduja needs an absent external robots-thesis header.\n# add_subdirectory(gianduja)',
                'Omit only an unrelated task family with an unavailable external dependency; Mate APC/NC/CC scorers are unchanged.', patch_records)
    write_json(logs / 'build_only_patches.json', patch_records)

    # Confirm that no archived source file changed except the three declared CMake files.
    allowed = {
        'epuck': {'src/CMakeLists.txt', 'src/plugins/robots/e-puck/CMakeLists.txt'},
        'metrics': {'loop-functions/CMakeLists.txt'},
    }
    integrity = []
    for key, source in extracted.items():
        changed = []
        checked = 0
        entry = entries[key]
        with zipfile.ZipFile(package / 'sources' / entry['filename']) as z:
            for item in z.infolist():
                if item.is_dir():
                    continue
                rel = PurePosixPath(item.filename).relative_to(entry['archive_root'])
                if not rel.parts:
                    continue
                path = source.joinpath(*rel.parts)
                expected = z.read(item)
                actual = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
                checked += 1
                if actual != expected:
                    changed.append(str(rel))
        unexpected = set(changed) - allowed.get(key, set())
        if unexpected:
            raise ValueError(f'Unexpected source modifications in {key}: {sorted(unexpected)}')
        integrity.append({'id': key, 'files_checked': checked, 'changed_files': changed, 'only_declared_build_changes': True})
    write_json(logs / 'source_integrity_before_build.json', integrity)

    if args.extract_only:
        print(json.dumps({'runtime_dir': str(runtime), 'extracted': {k: str(v) for k, v in extracted.items()}, 'built': False}, indent=2))
        return 0
    if not args.cmake:
        raise ValueError('CMake is not installed. Provide --cmake /path/to/cmake (3.x; tested 3.27.9).')
    cmake = shutil.which(args.cmake) or str(Path(args.cmake).expanduser().resolve())
    version_output = subprocess.check_output([cmake, '--version'], text=True).splitlines()[0]
    if not re.search(r'version 3\.', version_output):
        raise ValueError(f'{version_output}: this legacy source kit requires CMake 3.x; use --cmake to select it.')
    for tool in ['make', 'g++', 'pkg-config']:
        if not shutil.which(tool):
            raise ValueError(f'Missing build prerequisite: {tool}; see BUILD_NOTES.txt.')

    prefix = runtime / 'prefix'
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = str(prefix / 'lib/pkgconfig') + (':' + env['PKG_CONFIG_PATH'] if env.get('PKG_CONFIG_PATH') else '')
    env['LD_LIBRARY_PATH'] = ':'.join([str(prefix / 'lib/argos3'), str(prefix / 'lib')] + ([env['LD_LIBRARY_PATH']] if env.get('LD_LIBRARY_PATH') else []))
    stages = [('argos', extracted['argos'] / 'src', True), ('epuck', extracted['epuck'] / 'src', True), ('dao', extracted['dao'], True), ('metrics', extracted['metrics'], True), ('mate', extracted['mate'], False)]
    common = ['-DCMAKE_INSTALL_PREFIX=' + str(prefix), '-DCMAKE_PREFIX_PATH=' + str(prefix), '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_STANDARD=11', '-DARGOS_INSTALL_LDSOCONF=OFF', '-DARGOS_DOCUMENTATION=OFF', '-DARGOS_BUILD_NATIVE=OFF', '-DCMAKE_DISABLE_FIND_PACKAGE_Qt5=TRUE', '-DCMAKE_DISABLE_FIND_PACKAGE_Qt4=TRUE', '-DCMAKE_DISABLE_FIND_PACKAGE_Lua52=TRUE']
    completed = []
    total_start = time.perf_counter()
    for name, source, install in stages:
        build = runtime / 'build' / name
        commands = [('configure', [cmake, '-S', str(source), '-B', str(build)] + common), ('build', [cmake, '--build', str(build), '--parallel', str(max(1, args.jobs))])]
        if install:
            commands.append(('install', [cmake, '--install', str(build)]))
        for phase, command in commands:
            log = logs / f'{name}_{phase}.log'
            print(f'START {name} {phase}', flush=True)
            start = time.perf_counter()
            with log.open('w') as f:
                result = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT)
            record = {'component': name, 'phase': phase, 'returncode': result.returncode, 'wall_seconds': time.perf_counter() - start, 'command': command, 'log': str(log)}
            completed.append(record)
            write_json(logs / 'build_steps.json', completed)
            print(json.dumps({k: record[k] for k in ['component', 'phase', 'returncode', 'wall_seconds']}), flush=True)
            if result.returncode:
                print(log.read_text(errors='replace')[-6000:], file=sys.stderr)
                return result.returncode

    models = {}
    for name in ['mate']:
        models[name] = {'version': entries[name]['version'], 'source_dir': str(extracted[name]), 'binary': str(extracted[name] / 'bin/automode_main'), 'library': str(runtime / 'build' / name / 'src/libautomode.so')}
    runtime_info = {
        'complete': True, 'runtime_dir': str(runtime), 'prefix': str(prefix), 'plugin_dir': str(prefix / 'lib/argos3'),
        'argos_binary': str(prefix / 'bin/argos3'), 'models': models,
        'metrics': {task: str(runtime / 'build/metrics/loop-functions/mate' / task.upper() / f'libmate_{task}_loopfunc.so') for task in ['apc', 'nc', 'cc']},
        'source_dirs': {k: str(v) for k, v in extracted.items()},
        'original_xml_dir': str(extracted['mate'] / 'optimization/experiments-folder'),
        'irace_archive': str(package / 'sources' / entries['irace']['filename']),
        'build': {'cmake': cmake, 'cmake_version': version_output, 'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0], 'platform': platform.platform(), 'jobs': args.jobs, 'total_wall_seconds': time.perf_counter() - total_start, 'logs_dir': str(logs)},
        'notes': ['No algorithm, objective or robot dynamics source edits.', 'Only three documented CMake compatibility changes; Unix ZIP symlinks preserved.', 'irace source bundled but not installed by this C++ bootstrap; R is a separate prerequisite.'],
    }
    file_paths = [Path(runtime_info['argos_binary'])] + [Path(v) for v in runtime_info['metrics'].values()]
    for model in models.values():
        file_paths += [Path(model['binary']), Path(model['library'])]
    runtime_info['binary_sha256'] = {str(p): sha256(p) for p in file_paths}
    write_json(runtime / 'runtime.json', runtime_info)
    print('BUILD COMPLETE: ' + str(runtime / 'runtime.json'), flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'Bootstrap stopped: {error}', file=sys.stderr)
        raise SystemExit(1)
