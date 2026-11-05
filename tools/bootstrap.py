"""Fetch development dependencies and prepare an inspection-only reference sheet."""
from pathlib import Path
import hashlib
import json
import urllib.request
from release_common import mod_version
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
(ROOT / 'libs').mkdir(exist_ok=True)
(ROOT / 'research').mkdir(exist_ok=True)

def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': f'BossesRiseDelight-development/{mod_version()}'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()

def mod(project, loader, target_version=None):
    query = '?loaders=%5B%22' + loader + '%22%5D&game_versions=%5B%221.21.1%22%5D'
    versions = json.loads(get(f'https://api.modrinth.com/v2/project/{project}/version{query}'))
    if target_version:
        versions = [version for version in versions if version['version_number'] == target_version or version['version_number'].endswith('-' + target_version)]
    version = next(v for v in versions if v['version_type'] == 'release')
    entry = next(f for f in version['files'] if f['primary'])
    dest = ROOT / 'libs' / entry['filename']
    if not dest.exists():
        data = get(entry['url'])
        assert hashlib.sha512(data).hexdigest() == entry['hashes']['sha512']
        dest.write_bytes(data)
    assert hashlib.sha512(dest.read_bytes()).hexdigest() == entry['hashes']['sha512'], f'Dependency checksum mismatch: {dest}'
    record = {'project': project, 'version': version['version_number'], 'url': entry['url'],
              'file': entry['filename'], 'sha512': entry['hashes']['sha512']}
    (ROOT / 'research' / f'{project}-dependency.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record))

if __name__ == '__main__':
    mod('farmers-delight', 'neoforge', '1.3.4')
    mod('geckolib', 'neoforge', '4.8.2')
    mod('bossesrise', 'neoforge', '2.1.2')
    examples = [
        ('FarmersDelight', 'farmersdelight', 'item', 'beef_stew'),
        ('FarmersDelight', 'farmersdelight', 'item', 'steak_and_potatoes'),
        ('FarmersDelight', 'farmersdelight', 'item', 'chicken_sandwich'),
        ('FarmersDelight', 'farmersdelight', 'item', 'honey_glazed_ham'),
        ('FarmersDelight', 'farmersdelight', 'item', 'iron_knife'),
        ('NethersDelight', 'nethersdelight', 'item', 'strider_slice'),
        ('NethersDelight', 'nethersdelight', 'item', 'grilled_strider'),
        ('NethersDelight', 'nethersdelight', 'item', 'strider_moss_stew'),
    ]
    ocean = ROOT / 'research/OceansDelight/src/main/resources/assets'
    for path in list(ocean.glob('*/textures/item/*.png'))[:4]:
        examples.append(('OceansDelight', path.parts[-4], 'item', path.stem))
    sheet = Image.new('RGB', (720, 440), '#292d32')
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 12), 'STYLE STUDY ONLY - original mod textures are NOT included in the addon', fill='#e8dac0')
    measurements = []
    for i, (repo, namespace, kind, name) in enumerate(examples):
        path = ROOT / f'research/{repo}/src/main/resources/assets/{namespace}/textures/{kind}/{name}.png'
        if not path.exists():
            continue
        sprite = Image.open(path).convert('RGBA')
        measurements.append({'source': repo, 'file': name, 'size': sprite.size,
                             'opaque_colors': len({p for p in sprite.getdata() if p[3] == 255})})
        x, y = 18 + (i % 6) * 118, 48 + (i // 6) * 184
        sheet.paste(sprite.resize((96, 96), Image.Resampling.NEAREST), (x, y), sprite.resize((96, 96), Image.Resampling.NEAREST))
        draw.text((x, y + 106), name[:19], fill='#f0e5cf')
        draw.text((x, y + 124), repo, fill='#a6b9b0')
    if measurements:
        sheet.save(ROOT / 'docs/texture-reference-study.png')
        (ROOT / 'docs/reference-measurements.json').write_text(json.dumps(measurements, indent=2), encoding='utf-8')
