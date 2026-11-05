"""Build, run real Forge GameTests and automatically review three development clients."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import hashlib
from release_common import mod_version, release_jar

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / 'build/verification'


def source_hash():
    digest = hashlib.sha256()
    paths = [*sorted((ROOT / 'src').rglob('*')), ROOT / 'build.gradle', ROOT / 'gradle.properties', ROOT / 'dependencies.lock.json']
    for path in paths:
        if path.is_file():
            digest.update(path.relative_to(ROOT).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def run(name, command, timeout=600):
    LOGS.mkdir(parents=True, exist_ok=True)
    print(f'Running {name}...', flush=True)
    with (LOGS / f'{name}.log').open('w', encoding='utf-8') as log:
        subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=timeout)
    return (LOGS / f'{name}.log').read_text(encoding='utf-8', errors='replace')


def main():
    run('dependencies', [sys.executable, 'tools/bootstrap.py'])
    run('assets', [sys.executable, 'tools/check_assets.py'])
    gradle = [str(ROOT / 'gradlew.bat')] if os.name == 'nt' else ['sh', str(ROOT / 'gradlew')]
    initial_hash = source_hash()
    text = run('game-tests', [*gradle, 'build', 'runGameTestServer', '--console=plain'])
    expected = len(re.findall(r'@GameTest\(', (ROOT / 'src/main/java/com/suiyi/bossesrisedelight/verification/DelightGameTests.java').read_text()))
    if f'All {expected} required tests passed' not in text or f'{expected} GAME TESTS COMPLETE' not in text:
        raise RuntimeError('Forge exited without the complete successful GameTest summary. Inspect build/verification/game-tests.log.')
    reviews = [('assetReview', 'asset-review.txt'), ('knifeReview', 'knife-review.txt'), ('knifeTooltipReview', 'knife-tooltip-review.txt')]
    for name, report in reviews:
        directory = ROOT / {'assetReview': 'run-asset-review', 'knifeReview': 'run-knife-review', 'knifeTooltipReview': 'run-knife-tooltip-review'}[name]
        directory.mkdir(exist_ok=True)
        options = directory / 'options.txt'
        if not options.exists():
            options.write_text('lang:zh_cn\nguiScale:1\nsoundCategory_master:0.0\n', encoding='utf-8')
        result = directory / report
        result.unlink(missing_ok=True)
        run(name, [*gradle, 'run' + name[0].upper() + name[1:], '--console=plain'])
        if not result.exists():
            raise RuntimeError(f'Client exited without producing {report}')
        (ROOT / 'docs' / report).write_bytes(result.read_bytes())
    assets = (ROOT / 'docs/asset-review.txt').read_text(encoding='utf-8')
    if not all(value in assets for value in ['Rendered items: 31', 'Missing models: []', 'Rendered effects: 13', 'Missing effects: []']):
        raise RuntimeError('Client reported missing assets')
    knives = (ROOT / 'docs/knife-review.txt').read_text(encoding='utf-8')
    if not all(value in knives for value in ['Held contexts checked: 8', 'Tip axis preserved: true', 'Blade edge reversed: true']):
        raise RuntimeError('Held knife transform review failed')
    tooltip = (ROOT / 'docs/knife-tooltip-review.txt').read_text(encoding='utf-8')
    if 'Tooltip items checked: 2' not in tooltip or '狩猎加成' not in tooltip:
        raise RuntimeError('Translated knife tooltip review failed')
    if initial_hash != source_hash():
        raise RuntimeError('Sources changed while verification was running; rerun verification')
    jar = release_jar()
    report = {'version': mod_version(), 'minecraft': '1.20.1', 'loader': 'Forge', 'forge': '47.4.20', 'java_target': 17,
              'game_tests': {'passed': expected, 'failed': 0},
              'client_models': {'passed': 31, 'missing': 0}, 'client_effect_icons': {'passed': 13, 'missing': 0},
              'held_knife_contexts': 8, 'translated_knife_tooltips': 2,
              'textures': 46, 'recipes': 31, 'source_sha256': initial_hash,
              'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
              'dependencies': json.loads((ROOT / 'dependencies.lock.json').read_text()),
              'limitations': ['No full survival balance playthrough', 'No multiplayer stress test'],
              'dependency_warnings': ['Bosses\'Rise sandworm geometry declares format 1.21.0; GeckoLib reports support for 1.12.0. The dependency is kept unmodified.']}
    (ROOT / 'docs/verification-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Passed {expected} GameTests, 31 item models, 13 effect icons, 8 held knife transforms and 2 translated tooltips.')


if __name__ == '__main__':
    main()
