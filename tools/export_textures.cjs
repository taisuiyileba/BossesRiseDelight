// Export the imagegen source atlas to Minecraft's native 16px grid.
// Tight silhouette extraction, centered native-pixel export and palette encoding.
// Outline/color edits belong to the imagegen source atlas; no copied mod art.
const path = require('path');
const fs = require('fs');
let sharp;
try { sharp = require('sharp'); }
catch { sharp = require('C:/Users/suiyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const root = path.resolve(__dirname, '..');
const source = path.join(root, 'docs/generated-sprite-atlas.png');
const out = path.join(root, 'src/main/resources/assets/bossesrise_delight/textures');
const names = [
  'raw_dragon_cut', 'raw_yeti_cut', 'raw_sandworm_fillet', 'raw_kraken_tentacle', 'roasted_dragon_cut', 'cooked_yeti_cut',
  'purified_sandworm_fillet', 'grilled_kraken_tentacle', 'dragon_skewer', 'dragon_curry', 'dragon_sandwich', 'yeti_stew',
  'yeti_dumplings', 'frosted_berry_tart', 'sandworm_wrap', 'desert_stew', 'sandworm_rice', 'kraken_calamari',
  'kraken_chowder', 'sea_noodles', 'dragonbone_knife', 'krakentooth_knife', 'hunters_feast_serving', 'kraken_hotpot_serving'
];
async function binaryPNG(data, width, height, destination, colors = 20) {
  for (let i = 0; i < data.length; i += 4) {
    data[i + 3] = data[i + 3] >= 128 ? 255 : 0;
    if (!data[i + 3]) data[i] = data[i + 1] = data[i + 2] = 0;
  }
  // Explicit median-cut encoding keeps native sprites within the chosen palette,
  // including runtimes whose PNG encoder does not enforce the palette option.
  const histogram = new Map();
  for (let i = 0; i < data.length; i += 4) if (data[i + 3]) {
    const key = [data[i], data[i + 1], data[i + 2]].join(',');
    const value = histogram.get(key) || { rgb: [data[i], data[i + 1], data[i + 2]], count: 0 };
    value.count++; histogram.set(key, value);
  }
  const boxes = [[...histogram.values()]];
  function spread(box) {
    const ranges = [0, 1, 2].map(c => Math.max(...box.map(v => v.rgb[c])) - Math.min(...box.map(v => v.rgb[c])));
    return { range: Math.max(...ranges), channel: ranges.indexOf(Math.max(...ranges)) };
  }
  while (boxes.length < colors - 1) {
    let choice = -1, largest = -1;
    boxes.forEach((box, i) => { const range = spread(box).range; if (box.length > 1 && range > largest) { largest = range; choice = i; } });
    if (choice < 0) break;
    const box = boxes.splice(choice, 1)[0], channel = spread(box).channel;
    box.sort((a, b) => a.rgb[channel] - b.rgb[channel]);
    const half = box.reduce((sum, v) => sum + v.count, 0) / 2;
    let sum = 0, cut = 1;
    for (let i = 0; i < box.length - 1; i++) { sum += box[i].count; cut = i + 1; if (sum >= half) break; }
    boxes.push(box.slice(0, cut), box.slice(cut));
  }
  const palette = boxes.map(box => {
    const total = box.reduce((sum, v) => sum + v.count, 0);
    return [0, 1, 2].map(c => Math.round(box.reduce((sum, v) => sum + v.rgb[c] * v.count, 0) / total));
  });
  for (let i = 0; i < data.length; i += 4) if (data[i + 3]) {
    let closest, distance = Infinity;
    for (const color of palette) { const d = color.reduce((s, v, c) => s + (v - data[i + c]) ** 2, 0); if (d < distance) { distance = d; closest = color; } }
    [data[i], data[i + 1], data[i + 2]] = closest;
  }
  await sharp(data, { raw: { width, height, channels: 4 } }).png({ palette: true, colours: colors, dither: 0 }).toFile(destination);
}
function isolateSprite(data, width, height) {
  const seen = new Uint8Array(width * height), groups = [];
  for (let start = 0; start < width * height; start++) {
    if (seen[start] || data[start * 4 + 3] < 128) continue;
    const group = [], queue = [start]; seen[start] = 1;
    while (queue.length) {
      const pixel = queue.pop(); group.push(pixel);
      const x = pixel % width, y = Math.floor(pixel / width);
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const xx = x + dx, yy = y + dy, next = yy * width + xx;
        if (xx >= 0 && xx < width && yy >= 0 && yy < height && !seen[next] && data[next * 4 + 3] >= 128) { seen[next] = 1; queue.push(next); }
      }
    }
    groups.push(group);
  }
  groups.sort((a, b) => b.length - a.length);
  const main = new Set(groups[0] || []);
  if (!main.size) throw new Error('No visible sprite found in atlas cell');
  for (let pixel = 0; pixel < width * height; pixel++) if (!main.has(pixel)) data[pixel * 4 + 3] = 0;
  return data;
}
function bounds(data, width, height) {
  let left = width, top = height, right = -1, bottom = -1;
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) if (data[(y * width + x) * 4 + 3] >= 128) {
    left = Math.min(left, x); top = Math.min(top, y);
    right = Math.max(right, x); bottom = Math.max(bottom, y);
  }
  if (right < left) throw new Error('Empty sprite bounds');
  return {left, top, width: right - left + 1, height: bottom - top + 1};
}
async function centeredSprite(cell, sourceWidth = 256, sourceHeight = 256, canvasSize = 16) {
  isolateSprite(cell, sourceWidth, sourceHeight);
  const sourceBounds = bounds(cell, sourceWidth, sourceHeight);
  const limit = canvasSize - 2;
  const scale = Math.min(limit / sourceBounds.width, limit / sourceBounds.height);
  const width = Math.max(1, Math.round(sourceBounds.width * scale));
  const height = Math.max(1, Math.round(sourceBounds.height * scale));
  const reduced = await sharp(cell, {raw: {width: sourceWidth, height: sourceHeight, channels: 4}})
    .extract(sourceBounds).resize(width, height, {kernel: 'nearest', fit: 'fill'}).ensureAlpha().raw().toBuffer();
  isolateSprite(reduced, width, height);
  const nativeBounds = bounds(reduced, width, height);
  const result = Buffer.alloc(canvasSize * canvasSize * 4);
  const left = Math.floor((canvasSize - nativeBounds.width) / 2), top = Math.floor((canvasSize - nativeBounds.height) / 2);
  for (let y = 0; y < nativeBounds.height; y++) for (let x = 0; x < nativeBounds.width; x++) {
    const index = ((y + nativeBounds.top) * width + x + nativeBounds.left) * 4;
    const target = ((y + top) * canvasSize + x + left) * 4;
    reduced.copy(result, target, index, index + 4);
  }
  return {data: result, sourceBounds, nativeBounds: {left, top, width: nativeBounds.width, height: nativeBounds.height}};
}
async function tile(name, column, row, crop) {
  const extracted = await sharp(source).extract({left: column * 256 + crop[0], top: row * 256 + crop[1], width: crop[2], height: crop[3]})
    .resize(16, 16, { kernel: 'nearest', fit: 'fill' }).ensureAlpha().raw().toBuffer();
  // Tiles use the opaque interior of their corresponding atlas sprites.
  for (let i = 0; i < extracted.length; i += 4) extracted[i + 3] = 255;
  await binaryPNG(extracted, 16, 16, path.join(out, 'block', name + '.png'), 12);
}
async function main() {
  fs.mkdirSync(path.join(out, 'item'), {recursive: true});
  fs.mkdirSync(path.join(out, 'block'), {recursive: true});
  const meta = await sharp(source).metadata();
  if (meta.width !== 1536 || meta.height !== 1024) throw new Error('Expected exact 6x4, 256px cell atlas');
  const placement = [];
  for (let i = 0; i < names.length; i++) {
    const cell = await sharp(source).extract({left: (i % 6) * 256, top: Math.floor(i / 6) * 256, width: 256, height: 256})
      .ensureAlpha().raw().toBuffer();
    const sprite = await centeredSprite(cell);
    await binaryPNG(sprite.data, 16, 16, path.join(out, 'item', names[i] + '.png'));
    placement.push({id: names[i], sourceBounds: sprite.sourceBounds, nativeBounds: sprite.nativeBounds});
  }
  fs.writeFileSync(path.join(root, 'docs/texture-placement.json'), JSON.stringify(placement, null, 2) + '\n');
  // Preserve established block-face tiles when editing only the inventory atlas.
  if (process.argv.includes('--block-tiles') || !fs.existsSync(path.join(out, 'block/roast.png'))) {
    await tile('roast', 4, 0, [100, 85, 80, 80]);
    await tile('tentacle', 3, 0, [148, 100, 40, 40]);
    await tile('broth', 5, 3, [100, 80, 50, 45]);
    await tile('metal', 5, 3, [82, 156, 60, 24]);
  }
  console.log('Exported 24 centered 16x16 item sprites; retained the 4 established block tiles.');
}
module.exports = {binaryPNG, centeredSprite};
if (require.main === module) main().catch(error => { console.error(error); process.exit(1); });
