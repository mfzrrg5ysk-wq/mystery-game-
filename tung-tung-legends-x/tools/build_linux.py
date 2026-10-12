"""Freeze and package the native game. Run from any current directory."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def audit(bundle,ceiling=(2,36)):
    highest=(0,)
    report=[]
    for path in bundle.rglob('*'):
        if not path.is_file():continue
        with path.open('rb') as f:
            if f.read(4)!=b'\x7fELF':continue
        text=subprocess.run(['readelf','--version-info',str(path)],check=True,capture_output=True,text=True).stdout
        versions=[tuple(map(int,x.split('.'))) for x in re.findall(r'GLIBC_(\d+(?:\.\d+)+)',text)]
        maximum=max(versions,default=(0,))
        highest=max(highest,maximum)
        if maximum>ceiling:raise RuntimeError(f'Chromebook-incompatible glibc dependency: {path.name} {maximum}')
        report.append(dict(file=str(path.relative_to(bundle)),glibc='.'.join(map(str,maximum))))
    return dict(maximum_glibc='.'.join(map(str,highest)),libraries=report)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-freeze',action='store_true')
    parser.add_argument('--glibc-ceiling',default='2.36',help='Maximum glibc supported by the target Chromebook Linux environment')
    args=parser.parse_args()
    if os.uname().machine!='x86_64':raise SystemExit('Build this executable on x86-64 Linux.')
    if not args.skip_freeze:
        cmd=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--name','TungTungLegendsX',
             '--add-data','assets:assets']
        for name in ['tkinter','numpy','PIL','scipy','matplotlib','pytest','IPython','pandas','pyarrow']:
            cmd+=['--exclude-module',name]
        cmd+=['game.py']
        subprocess.run(cmd,cwd=ROOT,check=True)
    bundle=ROOT/'dist'/'TungTungLegendsX'
    for name in ['libstdc++.so.6','libgcc_s.so.1']:
        # pygame's manylinux libs need only GLIBCXX_3.4.19. Do not distribute
        # an Ubuntu build-machine C++ runtime that needs newer glibc than Debian.
        path=bundle/'_internal'/name
        if path.exists() or path.is_symlink():path.unlink()
    license_dir=bundle/'licenses'
    license_dir.mkdir(exist_ok=True)
    for filename in ['GPL-2','LGPL-2.1','LGPL-3','Apache-2.0','BSD','GFDL-1.3']:
        source=Path('/usr/share/common-licenses')/filename
        if source.exists():shutil.copy2(source,license_dir/filename)
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.exists():shutil.copy2(python_license,license_dir/'PYTHON-LICENSE.txt')
    for file in importlib.metadata.distribution('pyinstaller').files:
        if str(file).endswith('licenses/COPYING.txt'):
            shutil.copy2(importlib.metadata.distribution('pyinstaller').locate_file(file),license_dir/'PYINSTALLER-COPYING.txt')
    for filename in ['LICENSE','THIRD-PARTY-NOTICES.md','README.md']:
        shutil.copy2(ROOT/filename,bundle/filename)
    shutil.copy2(ROOT/'assets'/'FONT-LICENSE.txt',license_dir/'FONT-LICENSE.txt')
    report=audit(bundle,tuple(map(int,args.glibc_ceiling.split('.'))))
    release=ROOT/'release'
    release.mkdir(exist_ok=True)
    (release/'compatibility-audit.json').write_text(json.dumps(report,indent=2))
    stage=ROOT/'release-staging'
    if stage.exists():shutil.rmtree(stage)
    appdir=stage/'opt'/'tung-tung-legends-x'
    appdir.parent.mkdir(parents=True)
    shutil.copytree(bundle,appdir,symlinks=True)
    bindir=stage/'usr'/'bin';bindir.mkdir(parents=True)
    command=bindir/'tung-tung-legends-x'
    command.write_text('#!/bin/sh\nexec /opt/tung-tung-legends-x/TungTungLegendsX "$@"\n')
    command.chmod(0o755)
    applications=stage/'usr'/'share'/'applications';applications.mkdir(parents=True)
    (applications/'tung-tung-legends-x.desktop').write_text(
        '[Desktop Entry]\nVersion=1.0\nType=Application\nName=Tung Tung TungLegendss X\n'
        'Comment=Farm tungs, hatch pets, rebirth and become Legend X\n'
        'Exec=tung-tung-legends-x\nIcon=tung-tung-legends-x\nTerminal=false\nCategories=Game;Simulation;\n')
    icons=stage/'usr'/'share'/'icons'/'hicolor'/'256x256'/'apps';icons.mkdir(parents=True)
    if (ROOT/'assets'/'icon.png').exists():shutil.copy2(ROOT/'assets'/'icon.png',icons/'tung-tung-legends-x.png')
    control=stage/'DEBIAN';control.mkdir()
    size=sum(f.stat().st_size for f in stage.rglob('*') if f.is_file())//1024
    glibc_floor='.'.join(map(str,max((2,28),tuple(map(int,report['maximum_glibc'].split('.'))))))
    (control/'control').write_text(
        'Package: tung-tung-legends-x\nVersion: 1.0.0\nSection: games\nPriority: optional\n'
        'Architecture: amd64\nMaintainer: Tung Tung TungLegendss X contributors\n'
        f'Installed-Size: {size}\n'
        f'Depends: libc6 (>= {glibc_floor}), libgcc-s1, libstdc++6 (>= 4.9), libx11-6, libxext6, libxrender1, libxrandr2, libxcursor1, libxi6, libxfixes3, libasound2\n'
        'Description: Native offline Tung farming and rebirth clicker simulator\n'
        ' Farm 1200 campaign stages, hatch multiplier pets, recruit heroes,\n'
        ' craft ability items, rebirth for souls and ascend for astrals.\n'
        ' Includes an independent desktop window and local save recovery.\n')
    deb=release/'TungTungLegendsX-Chromebook-Linux.deb'
    subprocess.run(['dpkg-deb','--root-owner-group','-Zxz','--build',str(stage),str(deb)],check=True)
    portable=release/'TungTungLegendsX-Linux-Portable.zip'
    prefix='TungTungLegendsX-Linux/'
    with zipfile.ZipFile(portable,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in bundle.rglob('*'):
            if f.is_file():z.write(f,prefix+'TungTungLegendsX/'+str(f.relative_to(bundle)))
        for filename in ['PLAY.sh','README.md','LICENSE','THIRD-PARTY-NOTICES.md']:
            z.write(ROOT/filename,prefix+filename)
        for path in source_paths():z.write(path,prefix+'source/'+str(path.relative_to(ROOT)))
        preview=ROOT/'assets'/'preview.png'
        if preview.exists():z.write(preview,prefix+'preview.png')
        z.write(release/'compatibility-audit.json',prefix+'compatibility-audit.json')
    hashes=[]
    for f in [deb,portable]:
        hashes.append(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name)
        print(f.name,round(f.stat().st_size/1048576,2),'MiB')
    (release/'SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n')
    print('Native compatibility audit passed. Maximum bundled glibc requirement:',report['maximum_glibc'])

def source_paths():
    for f in ROOT.rglob('*'):
        relative=f.relative_to(ROOT)
        if any(p in ['dist','build','release','release-staging','__pycache__','.venv','licenses'] for p in relative.parts):continue
        if not f.is_file() or f.name in ['build-log.txt'] or f.suffix in ['.pyc','.spec']:continue
        yield f

if __name__=='__main__':main()
