// Export only the new Nether Knight sprites and original status icons.
const fs = require('fs');
const path = require('path');
let sharp;
try { sharp = require('sharp'); } catch { sharp = require('C:/Users/suiyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const {binaryPNG, centeredSprite} = require('./export_textures.cjs');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'src/main/resources/assets/bossesrise_delight/textures');
async function atlas(filename, columns, rows, names, folder, size) {
  const file = path.join(root, 'docs', filename);
  const info = await sharp(file).metadata();
  fs.mkdirSync(path.join(out, folder), {recursive: true});
  for (let i = 0; i < names.length; i++) {
    const column = i % columns, row = Math.floor(i / columns);
    const left = Math.round(column * info.width / columns), top = Math.round(row * info.height / rows);
    const width = Math.round((column + 1) * info.width / columns) - left;
    const height = Math.round((row + 1) * info.height / rows) - top;
    const cell = await sharp(file).extract({left, top, width, height}).ensureAlpha().raw().toBuffer();
    const sprite = await centeredSprite(cell, width, height, size);
    await binaryPNG(sprite.data, size, size, path.join(out, folder, names[i] + '.png'));
  }
}
async function main() {
  await atlas('nether-food-atlas.png', 3, 2, ['nether_ember', 'soul_salt', 'soul_braised_meat', 'soulfire_noodles', 'nightwatch_pie'], 'item', 16);
  await atlas('effect-atlas.png', 4, 4, ['ember_appetite', 'blaze_digest', 'frost_shell', 'frost_reprisal', 'sand_surge', 'venom_sac', 'tidal_echo', 'abyss_gills', 'soul_harvest', 'nether_resolve', 'hunter_resonance', 'rimebound', 'corrosive_venom'], 'mob_effect', 18);
  console.log('Exported 5 new centered food/seasoning sprites and 13 native 18px effect icons. Existing approved textures are unchanged.');
}
main().catch(error => {console.error(error); process.exit(1);});
