"""Collect only original project files and write reproducible release verification records."""
from pathlib import Path
import json
import hashlib
import shutil
import zipfile
import re

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'release'
RELEASE.mkdir(exist_ok=True)
properties = dict(line.split('=', 1) for line in (ROOT / 'gradle.properties').read_text(encoding='utf-8').splitlines() if '=' in line and not line.startswith('#'))
version = properties['mod_version']
content = json.loads((ROOT / 'docs/content-summary.json').read_text(encoding='utf-8'))
jar = ROOT / f'build/libs/bossesrise-delight-1.21.1-neoforge-{version}.jar'
with zipfile.ZipFile(jar) as archive:
    entries = archive.namelist()
    assert not any('/verification/' in name for name in entries), 'Development test classes must not ship'
    assert not any(name.startswith(('vectorwing/', 'net/unusual/', 'software/bernie/')) for name in entries), 'Third-party dependency classes must not ship'
    assert not any(name.endswith('/empty.nbt') for name in entries), 'Test template must not ship'
    assert 'META-INF/LICENSE' in entries
    assert f'version="{version}"'.encode() in archive.read('META-INF/neoforge.mods.toml')
    textures = [name for name in entries if '/textures/' in name and name.endswith('.png')]
    recipes = [name for name in entries if '/recipe/' in name and name.endswith('.json')]
    assert len(textures) == content['textures'] and len(recipes) == content['recipes']
    assert 'data/bossesrise_delight/recipe/cutting/hunters_feast.json' not in entries
    assert 'data/bossesrise_delight/recipe/cutting/kraken_hotpot.json' not in entries
shutil.copy2(jar, RELEASE / jar.name)
shutil.copy2(ROOT / f'build/libs/bossesrise-delight-1.21.1-neoforge-{version}-sources.jar', RELEASE)

log = (ROOT / 'run-gametest/logs/latest.log').read_text(encoding='utf-8')
matches = re.findall(r'All (\d+) required tests passed', log)
assert matches, 'Game tests must all pass'
test_count = int(matches[-1])
assert test_count >= 20
review = (ROOT / 'run-asset-review/asset-review.txt').read_text(encoding='utf-8')
assert f'Rendered items: {content["items"]}' in review and 'Missing models: []' in review
assert f'Rendered effects: {content["effects"]}' in review and 'Missing effects: []' in review
validation = json.loads((ROOT / 'docs/asset-validation.json').read_text(encoding='utf-8'))
assert not validation['errors']
dependencies = [json.loads(path.read_text(encoding='utf-8')) for path in (ROOT / 'research').glob('*-dependency.json')]
report = {'version': version, 'minecraft': '1.21.1', 'neoforge_tested': '21.1.248',
          'dependencies': dependencies, 'game_tests': {'passed': test_count, 'failed': 0},
          'recipes': len(recipes), 'textures': len(textures), 'rendered_items': content['items'], 'rendered_effect_icons': content['effects'],
          'missing_item_models': [], 'texture_validation_errors': [], 'texture_metrics': validation.get('summary', {}),
          'test_scope': ['Recipe loading and Farmer\'s Delight recipe matching', 'Stacked meal bowl return and effect application',
                         'Container conservation for both feasts and removal of invalid cutting recipes', 'All five original boss loot tables, player-kill condition and knife bonus',
                         'All custom meal profiles and full-hunger consumption', 'Ember combo, frost shield regeneration, reprisal and proc cooldowns',
                         'Sprint burst, corrosive damage over time and nonrecursive delayed echo', 'Underwater air recovery and oxygen-based defense',
                         'War-soul lethal guard, absorption compatibility and void behavior', 'Low-health counter window, hostile-kill healing and player proc rules',
                         'Actual client rendering of all item models and original effect icons'],
          'limitations': ['No full survival balance playthrough yet', 'No multiplayer stress test yet', 'Only Minecraft 1.21.1 / NeoForge is implemented'],
          'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest()}
test_version = re.search(r"Bosses'Rise Delight ([^\s]+) \(bossesrise_delight\)", log)
report['game_tests']['tested_version'] = test_version.group(1) if test_version else 'not recorded'
knife_review_file = ROOT / 'docs/knife-review.txt'
if knife_review_file.exists():
    knife_review = knife_review_file.read_text(encoding='utf-8')
    assert 'Held contexts checked: 8' in knife_review
    assert 'Tip axis preserved: true' in knife_review and 'Blade edge reversed: true' in knife_review
    report['knife_held_model_checks'] = {'passed': 8, 'tip_axis_preserved': True, 'blade_edge_reversed': True}
    report['test_scope'].append('Both chef knives in first/third-person left/right hand transforms, with actual Minecraft rendering')
tooltip_review_file = ROOT / 'docs/knife-tooltip-review.txt'
if tooltip_review_file.exists():
    tooltip_review = tooltip_review_file.read_text(encoding='utf-8')
    assert 'Tooltip items checked: 2' in tooltip_review and '狩猎加成' in tooltip_review
    report['knife_tooltip_checks'] = {'passed': 2, 'translated_hunting_bonus_visible': True}
    report['test_scope'].append('Actual translated inventory tooltips for both knives, including hunting amount, main-hand condition and cutting distinction')
(ROOT / 'docs/verification-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
(RELEASE / 'verification-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

excluded = {'.gradle', 'build', 'research', 'libs', 'release', 'run-client', 'run-server', 'run-gametest', 'run-asset-review', 'run-knife-review', 'run-knife-tooltip-review', '__pycache__'}
source_zip = RELEASE / f'bossesrise-delight-{version}-project.zip'
with zipfile.ZipFile(source_zip, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if path.is_file() and not any(part in excluded for part in relative.parts):
            archive.write(path, Path('BossesRiseDelight') / relative)
checksums = '\n'.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}' for path in sorted(RELEASE.iterdir()) if path.suffix in {'.jar', '.zip'}) + '\n'
(RELEASE / 'SHA256SUMS.txt').write_text(checksums, encoding='utf-8')
print(f'Packaged {jar.name}: {jar.stat().st_size} bytes; verified {test_count} game tests, {content["items"]} items, {content["effects"]} effect icons, {len(recipes)} recipes and {len(textures)} textures.')
