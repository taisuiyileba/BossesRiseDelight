"""Preview or upload built Bosses'Rise Delight releases to CurseForge.

Based on the MobSpawnController publisher. No third-party Python packages required.
API: https://support.curseforge.com/support/solutions/articles/9000197321
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import struct
import urllib.error
import urllib.request
import uuid
import zipfile
from release_common import ROOT, mod_version, release_config, release_jar

API = 'https://minecraft.curseforge.com/api'


def prepare(root):
    config = release_config(root)
    version = mod_version(root)
    jar = release_jar(root)
    changelog = (root / f'CHANGELOG-{version}.md').read_text(encoding='utf-8').strip()
    if not changelog.startswith(f'# {version}\n'):
        raise ValueError(f'Changelog heading does not match {version}')
    metadata_file = 'META-INF/' + ('mods.toml' if config['loader'] == 'Forge' else 'neoforge.mods.toml')
    with zipfile.ZipFile(jar) as archive:
        names = archive.namelist()
        metadata = archive.read(metadata_file).decode('utf-8')
        embedded_version = re.search(r'^version\s*=\s*"([^"]+)"', metadata, re.MULTILINE)
        if not embedded_version or embedded_version.group(1) != version:
            raise ValueError(f'{jar.name}: embedded mod version does not match {version}')
        if not re.search(r'^modId\s*=\s*"bossesrise_delight"', metadata, re.MULTILINE):
            raise ValueError(f'{jar.name}: incorrect mod ID')
        if any('/verification/' in name or name.endswith('/empty.nbt') or
               name.startswith(('net/unusual/', 'vectorwing/', 'software/bernie/')) for name in names):
            raise ValueError(f'{jar.name}: development or dependency classes are present')
        for name in names:
            if name.endswith('.class'):
                major = struct.unpack('>H', archive.read(name)[6:8])[0]
                if major != config['java'] + 44:
                    raise ValueError(f'{jar.name}: incorrect Java bytecode version in {name}')
    metadata = {
        'changelog': changelog,
        'changelogType': 'markdown',
        'displayName': jar.name,
        'gameVersions': config['game_versions'],
        'releaseType': 'release',
        'relations': {'projects': [
            {'slug': slug, 'type': 'requiredDependency'} for slug in config['dependencies']]},
    }
    return {
        'root': root, 'config': config, 'version': version, 'jar': jar, 'metadata': metadata,
        'sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
        'metadata_sha256': hashlib.sha256(json.dumps(metadata, sort_keys=True).encode('utf-8')).hexdigest(),
    }


def load_token(path=None):
    token = os.environ.get('CURSEFORGE_API_TOKEN', '').strip()
    if not token:
        path = path or ROOT / 'api_tokens.json'
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        token = value['curseforge']['token'].strip()
    if not token:
        raise ValueError('Provide CURSEFORGE_API_TOKEN or --tokens with a configured curseforge.token')
    return token


def validate_game_versions(plans, token):
    request = urllib.request.Request(API + '/game/versions', headers={
        'X-Api-Token': token, 'User-Agent': 'BossesRiseDelight-release'})
    with urllib.request.urlopen(request, timeout=45) as response:
        versions = {entry['id']: entry['name'] for entry in json.load(response)}
    for plan in plans:
        config = plan['config']
        expected = [config['minecraft'], config['loader'], 'Client', 'Server', f"Java {config['java']}"]
        actual = [versions.get(identifier) for identifier in config['game_versions']]
        if actual != expected:
            raise ValueError(f"CurseForge version tags do not match {config['minecraft']} / {config['loader']}: {actual}")


def multipart(metadata, jar):
    boundary = 'BossesRiseDelight-' + uuid.uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="metadata"\r\n'
        'Content-Type: application/json; charset=utf-8\r\n\r\n'
    ).encode('utf-8')
    body += json.dumps(metadata, ensure_ascii=False).encode('utf-8')
    body += (
        f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{jar.name}"\r\n'
        'Content-Type: application/java-archive\r\n\r\n'
    ).encode('utf-8')
    body += jar.read_bytes() + f'\r\n--{boundary}--\r\n'.encode('ascii')
    return body, f'multipart/form-data; boundary={boundary}'


def save_receipt(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def upload(plan, token):
    config = plan['config']
    receipt_path = plan['root'] / 'release' / f"curseforge-{plan['version']}.json"
    identity = {key: plan[key] for key in ['version', 'sha256', 'metadata_sha256']}
    identity.update(project_id=config['project_id'], filename=plan['jar'].name)
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text(encoding='utf-8'))
        if any(previous.get(key) != value for key, value in identity.items()):
            raise ValueError(f'Release differs from the previous upload receipt: {receipt_path}')
        if previous.get('file_id'):
            print(f"Already uploaded: {previous['url']}")
            return previous
        if previous.get('status') in ['uploading', 'unknown']:
            raise ValueError(f'Previous upload outcome needs checking on CurseForge before retrying: {receipt_path}')
    body, content_type = multipart(plan['metadata'], plan['jar'])
    request = urllib.request.Request(
        f"{API}/projects/{config['project_id']}/upload-file", data=body, method='POST', headers={
            'X-Api-Token': token, 'Content-Type': content_type,
            'User-Agent': f"BossesRiseDelight-release/{plan['version']}",
        })
    receipt = dict(identity, status='uploading')
    save_receipt(receipt_path, receipt)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        file_id = result.get('id')
        if not isinstance(file_id, int) or file_id <= 0:
            raise ValueError('Upload response did not contain a valid CurseForge file ID')
    except urllib.error.HTTPError as error:
        receipt.update(status='failed', http_status=error.code)
        save_receipt(receipt_path, receipt)
        raise RuntimeError(f"CurseForge rejected {plan['jar'].name}: HTTP {error.code}") from None
    except (OSError, ValueError):
        receipt['status'] = 'unknown'
        save_receipt(receipt_path, receipt)
        raise
    receipt.update(status='uploaded', file_id=file_id,
                   url=f"https://www.curseforge.com/minecraft/mc-mods/{config['slug']}/files/{file_id}")
    save_receipt(receipt_path, receipt)
    print(f"Uploaded: {receipt['url']}")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Include sibling BossesRiseDelight versions')
    parser.add_argument('--upload', action='store_true', help='Upload after validation; default only previews metadata')
    parser.add_argument('--tokens', type=Path, help='MobSpawnController-compatible api_tokens.json; never copied or logged')
    args = parser.parse_args()
    roots = [ROOT]
    if args.all:
        project_id = release_config()['project_id']
        roots = [path for path in sorted(ROOT.parent.glob('BossesRiseDelight-*'))
                 if (path / 'curseforge.json').is_file() and release_config(path)['project_id'] == project_id]
    plans = [prepare(root) for root in roots]
    if len({plan['version'] for plan in plans}) != 1:
        raise ValueError('All targets must use the same mod version')
    for plan in plans:
        print(json.dumps({
            'project_id': plan['config']['project_id'], 'jar': str(plan['jar']),
            'sha256': plan['sha256'], 'metadata': plan['metadata'],
        }, indent=2, ensure_ascii=False))
    if not args.upload:
        print('Preview complete. Use --upload to publish these files.')
        return
    token = load_token(args.tokens)
    validate_game_versions(plans, token)
    for plan in plans:
        upload(plan, token)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, zipfile.BadZipFile) as error:
        raise SystemExit(str(error)) from None
