"""Shared version and artifact paths for release tools."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def mod_version(root=ROOT):
    for line in (root / 'gradle.properties').read_text(encoding='utf-8').splitlines():
        key, separator, value = line.partition('=')
        if separator and key.strip() == 'mod_version':
            return value.strip()
    raise ValueError('mod_version is missing from gradle.properties')


def release_config(root=ROOT):
    return json.loads((root / 'curseforge.json').read_text(encoding='utf-8'))


def release_jar(root=ROOT):
    return root / 'build/libs' / f"{release_config(root)['artifact']}-{mod_version(root)}.jar"


def project_files(root=ROOT):
    """Archive source files selected by Git, honoring .gitignore for new files."""
    result = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root)
    return [root / name for name in sorted(set(result.decode('utf-8').split('\0')))
            if name and (root / name).is_file()]
