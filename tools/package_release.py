"""Package the reobfuscated jar only when it matches the verified source and artifact hashes."""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import zipfile
from verify import source_hash
from release_common import mod_version, release_jar, project_files

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'release'


def main():
    report = json.loads((ROOT / 'docs/verification-report.json').read_text(encoding='utf-8'))
    version = mod_version()
    jar = release_jar()
    if report['source_sha256'] != source_hash() or report['jar_sha256'] != hashlib.sha256(jar.read_bytes()).hexdigest():
        raise RuntimeError('Sources or jar changed after verification; run tools/verify.py again')
    smoke_path = ROOT / 'docs/production-server-test.json'
    if smoke_path.exists():
        smoke = json.loads(smoke_path.read_text())
        if smoke['status'] != 'passed' or smoke['jar_sha256'] != report['jar_sha256']:
            raise RuntimeError('Production server result does not match the verified jar')
        report['production_server'] = smoke
        (ROOT / 'docs/verification-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with zipfile.ZipFile(jar) as archive:
        names = archive.namelist()
        if any('/verification/' in name or name.endswith('empty.nbt') or name.startswith(('net/unusual/', 'vectorwing/', 'software/bernie/')) for name in names):
            raise RuntimeError('Development tests or dependency classes leaked into the release jar')
        for name in names:
            if name.endswith('.class') and struct.unpack('>H', archive.read(name)[6:8])[0] != 61:
                raise RuntimeError(f'Class is not compiled for Java 17: {name}')
        if 'META-INF/mods.toml' not in names or 'META-INF/neoforge.mods.toml' in names:
            raise RuntimeError('Incorrect Forge metadata')
        if f'version="{version}"'.encode() not in archive.read('META-INF/mods.toml'):
            raise RuntimeError('Jar version does not match gradle.properties')
    RELEASE.mkdir(exist_ok=True)
    for source in [jar, ROOT / 'README.md', ROOT / 'LICENSE', ROOT / 'dependencies.lock.json', ROOT / 'docs/verification-report.json', ROOT / f'CHANGELOG-{version}.md']:
        shutil.copy2(source, RELEASE / source.name)
    archive_path = RELEASE / f'bossesrise-delight-1.20.1-forge-{version}-project.zip'
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in project_files():
            relative = path.relative_to(ROOT)
            archive.write(path, Path('BossesRiseDelight-1.20.1forge') / relative)
    files = [RELEASE / jar.name, archive_path]
    (RELEASE / 'SHA256SUMS.txt').write_text('\n'.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}' for path in files) + '\n')
    print(f'Packaged verified Java 17 / Forge release: {jar.name}')


if __name__ == '__main__':
    main()
