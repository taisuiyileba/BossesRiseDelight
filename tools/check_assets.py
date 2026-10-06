"""Check shipped resource references, palette limits, dependency IDs and display an item contact sheet."""
from pathlib import Path
import json
import zipfile
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'src/main/resources'
MOD = 'bossesrise_delight'
errors = []

catalogue = json.loads((ROOT / 'docs/food-catalogue.json').read_text(encoding='utf-8'))
for path in RES.rglob('*.json'):
    try: json.loads(path.read_text(encoding='utf-8'))
    except Exception as error: errors.append(f'{path}: {error}')

dependency_files = {}
for path in [*list((ROOT / 'libs').glob('*.jar')), Path.home() / '.gradle/caches/forge_gradle/minecraft_repo/versions/1.20.1/client.jar']:
    if path.exists():
        with zipfile.ZipFile(path) as archive: dependency_files.update({name: path.name for name in archive.namelist()})

measurements = []
for path in (RES / f'assets/{MOD}/textures').rglob('*.png'):
    im = Image.open(path).convert('RGBA')
    pixels = list(im.get_flattened_data())
    alpha = {p[3] for p in pixels}
    colors = len({p[:3] for p in pixels if p[3]})
    expected_size = (18, 18) if path.parent.name == 'mob_effect' else (16, 16)
    if im.size != expected_size: errors.append(f'{path.name}: non-native texture dimensions {im.size}')
    if not alpha <= {0, 255}: errors.append(f'{path.name}: soft alpha found')
    if colors > 20: errors.append(f'{path.name}: palette exceeds 20 colors ({colors})')
    if not any(p[3] for p in pixels): errors.append(f'{path.name}: blank texture')
    entry = {'file': path.name, 'size': im.size, 'colors': colors, 'alpha': sorted(alpha)}
    if path.parent.name == 'item':
        bounds = im.getbbox()
        left, top, right, bottom = bounds
        padding = {'left': left, 'top': top, 'right': 16 - right, 'bottom': 16 - bottom}
        opaque = sum(pixel[3] > 0 for pixel in pixels)
        near_black = sum(pixel[3] > 0 and max(pixel[:3]) < 55 for pixel in pixels)
        entry.update({'bounds': bounds, 'padding': padding, 'near_black_pixels': near_black,
                      'opaque_pixels': opaque, 'near_black_percent': round(100 * near_black / opaque, 2)})
        if min(padding.values()) < 1: errors.append(f'{path.name}: silhouette reaches the canvas edge')
        if abs(padding['left'] - padding['right']) > 1 or abs(padding['top'] - padding['bottom']) > 1:
            errors.append(f'{path.name}: unbalanced margins {padding}')
        if near_black / opaque > .08: errors.append(f'{path.name}: excessive near-black pixels ({entry["near_black_percent"]}%)')
    measurements.append(entry)

for path in (RES / f'assets/{MOD}/models').rglob('*.json'):
    for texture in json.loads(path.read_text(encoding='utf-8')).get('textures', {}).values():
        if texture.startswith('#'): continue
        namespace, asset = texture.split(':')
        filename = f'assets/{namespace}/textures/{asset}.png'
        if not (RES / filename).exists() and filename not in dependency_files:
            errors.append(f'{path.name}: missing texture {texture}')

seasonings = json.loads((ROOT / 'docs/seasoning-catalogue.json').read_text(encoding='utf-8'))
effects = json.loads((ROOT / 'docs/effect-catalogue.json').read_text(encoding='utf-8'))
names = [f['id'] for f in catalogue] + [f['id'] for f in seasonings] + ['dragonbone_knife', 'krakentooth_knife']
sheet = Image.new('RGB', (1000, 94 + math.ceil(len(names) / 6) * 145), '#222c30')
draw = ImageDraw.Draw(sheet)
font_path = Path('C:/Windows/Fonts/msyh.ttc')
font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
draw.text((24, 18), "BOSSES'RISE DELIGHT  /  16 x 16 ORIGINAL PIXEL TEXTURES", fill='#efe5cf', font=font)
draw.text((24, 48), '5 条首领路线 · 15 道料理 · 11 种专属增益 · 2 种共享宴席', fill='#8ea9a3', font=font)
translations = json.loads((RES / f'assets/{MOD}/lang/zh_cn.json').read_text(encoding='utf-8'))
for i, name in enumerate(names):
    im = Image.open(RES / f'assets/{MOD}/textures/item/{name}.png').convert('RGBA').resize((80, 80), Image.Resampling.NEAREST)
    x, y = 28 + (i % 6) * 163, 94 + (i // 6) * 145
    sheet.paste(im, (x + 30, y), im)
    draw.text((x, y + 86), translations.get(f'item.{MOD}.{name}', name), fill='#e6d9be', font=font)
    draw.text((x, y + 110), '16px / no smoothing', fill='#79938e')
sheet.save(ROOT / 'docs/texture-preview.png')
effect_sheet = Image.new('RGB', (1000, 80 + math.ceil(len(effects) / 4) * 140), '#222c30')
effect_draw = ImageDraw.Draw(effect_sheet)
effect_draw.text((24, 18), '首领乐事 · 自创效果图标', fill='#efe5cf', font=font)
effect_draw.text((24, 48), '战斗触发、霜盾、腐毒、延迟追击与战魂护命', fill='#8ea9a3', font=font)
for i, effect in enumerate(effects):
    path = RES / f'assets/{MOD}/textures/mob_effect/{effect["id"]}.png'
    if not path.exists(): errors.append(f'missing custom effect icon: {effect["id"]}'); continue
    sprite = Image.open(path).convert('RGBA').resize((72, 72), Image.Resampling.NEAREST)
    x, y = 30 + (i % 4) * 246, 84 + (i // 4) * 140
    effect_sheet.paste(sprite, (x + 48, y), sprite)
    effect_draw.text((x, y + 80), effect['zh'], fill='#e6d9be', font=font)
    effect_draw.text((x, y + 104), effect['id'], fill='#79938e')
effect_sheet.save(ROOT / 'docs/effect-preview.png')
item_metrics = [m for m in measurements if 'near_black_pixels' in m]
summary = {'centered_sprites': sum(abs(m['padding']['left'] - m['padding']['right']) <= 1 and abs(m['padding']['top'] - m['padding']['bottom']) <= 1 for m in item_metrics),
           'near_black_percent': round(100 * sum(m['near_black_pixels'] for m in item_metrics) / sum(m['opaque_pixels'] for m in item_metrics), 2)}
(ROOT / 'docs/asset-validation.json').write_text(json.dumps({'errors': errors, 'summary': summary, 'textures': measurements}, indent=2), encoding='utf-8')
before_path = ROOT / 'docs/archive/0.1.0/textures/item'
if before_path.exists():
    selected = ['raw_dragon_cut', 'raw_yeti_cut', 'roasted_dragon_cut', 'cooked_yeti_cut',
                'dragon_skewer', 'frosted_berry_tart', 'raw_kraken_tentacle', 'kraken_chowder',
                'sea_noodles', 'kraken_hotpot_serving', 'dragonbone_knife', 'krakentooth_knife']
    comparison = Image.new('RGB', (1000, 710), '#eef0e9')
    compare_draw = ImageDraw.Draw(comparison)
    compare_draw.text((22, 16), '贴图调整对比：左为 0.1.0，右为新版', fill='#374b47', font=font)
    for i, name in enumerate(selected):
        x, y = 28 + (i % 3) * 328, 64 + (i // 3) * 159
        compare_draw.text((x, y), translations[f'item.{MOD}.{name}'], fill='#374b47', font=font)
        for j, path in enumerate([before_path / (name + '.png'), RES / f'assets/{MOD}/textures/item/{name}.png']):
            px, py = x + j * 136, y + 28
            compare_draw.rectangle((px, py, px + 96, py + 96), fill='#dbe0d6')
            compare_draw.line((px + 48, py, px + 48, py + 96), fill='#bcc9bf')
            compare_draw.line((px, py + 48, px + 96, py + 48), fill='#bcc9bf')
            sprite = Image.open(path).convert('RGBA').resize((96, 96), Image.Resampling.NEAREST)
            comparison.paste(sprite, (px, py), sprite)
    comparison.save(ROOT / 'docs/texture-comparison.png')
print(f'Validated {len(measurements)} textures and all model texture references; {len(errors)} errors.')
print(f'Centered item sprites: {summary["centered_sprites"]}/{len(names)}; near-black pixels: {summary["near_black_percent"]}%.')
if errors:
    print('\n'.join(errors)); raise SystemExit(1)
