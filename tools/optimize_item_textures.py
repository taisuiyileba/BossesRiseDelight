"""
Optimize item textures from docs/generated-sprite-atlas.png.
Transforms continuous-tone / noisy downscaled sprites into crisp,
readable, authentic Minecraft / Farmer's Delight 16x16 pixel art.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label, binary_fill_holes
from scipy.cluster.vq import kmeans2

ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = ROOT / 'docs/generated-sprite-atlas.png'
NETHER_ATLAS_PATH = ROOT / 'docs/nether-food-atlas.png'
ITEM_OUT = ROOT / 'src/main/resources/assets/bossesrise_delight/textures/item'
DOCS_DIR = ROOT / 'docs'

NAMES = [
    'raw_dragon_cut', 'raw_yeti_cut', 'raw_sandworm_fillet', 'raw_kraken_tentacle',
    'roasted_dragon_cut', 'cooked_yeti_cut', 'purified_sandworm_fillet', 'grilled_kraken_tentacle',
    'dragon_skewer', 'dragon_curry', 'dragon_sandwich', 'yeti_stew',
    'yeti_dumplings', 'frosted_berry_tart', 'sandworm_wrap', 'desert_stew',
    'sandworm_rice', 'kraken_calamari', 'kraken_chowder', 'sea_noodles',
    'dragonbone_knife', 'krakentooth_knife', 'hunters_feast_serving', 'kraken_hotpot_serving'
]

NETHER_ITEMS = [
    ('nether_ember', 0, 0, 1.25, 1.22, 11, None, 24),
    ('soul_salt', 0, 1, 1.20, 1.18, 11, (12, 14), 24),
    ('soul_braised_meat', 0, 2, 1.18, 1.15, 11, (14, 12), 24),
    ('soulfire_noodles', 1, 0, 1.18, 1.15, 12, (14, 12), 24),
    ('nightwatch_pie', 1, 1, 1.15, 1.12, 11, (14, 12), 24),
]

def isolate_main_component(arr, threshold=120):
    mask = arr[:, :, 3] >= threshold
    labeled, num_features = label(mask)
    if num_features == 0:
        return arr, None
    sizes = [np.sum(labeled == (j + 1)) for j in range(num_features)]
    max_idx = np.argmax(sizes) + 1
    main_mask = (labeled == max_idx)
    arr[~main_mask] = 0
    y_idx, x_idx = np.where(main_mask)
    bbox = (int(x_idx.min()), int(y_idx.min()), int(x_idx.max() + 1), int(y_idx.max() + 1))
    return arr, bbox

def remove_orphan_pixels(alpha):
    """Remove pixels that don't have enough 4-connected or 8-connected neighbors."""
    h, w = alpha.shape
    cleaned = alpha.copy()
    for y in range(h):
        for x in range(w):
            if not alpha[y, x]:
                continue
            # Count 4-connected neighbors
            n4 = 0
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and alpha[ny, nx]:
                    n4 += 1
            # If a pixel has 0 direct 4-neighbors, it's completely isolated
            if n4 == 0:
                cleaned[y, x] = False
    # Keep only the largest connected component
    labeled, num = label(cleaned, structure=np.ones((3, 3)))
    if num > 1:
        sizes = [np.sum(labeled == (j + 1)) for j in range(num)]
        max_idx = np.argmax(sizes) + 1
        cleaned = (labeled == max_idx)
    return cleaned

def optimize_texture(cell, name, tw_th=None, c_boost=1.32, s_boost=1.25, k=None, merge_dist=28):
    arr = np.array(cell)
    arr, bbox = isolate_main_component(arr)
    if bbox is None:
        raise ValueError(f"Failed to isolate sprite for {name}")
    
    sprite = Image.fromarray(arr).crop(bbox)
    sw, sh = sprite.size
    
    # Target dimensions: 14x14 max to ensure 1px padding in 16x16
    if tw_th is not None:
        tw, th = tw_th
    elif name == 'hunters_feast_serving':
        tw, th = 14, 10
    else:
        scale = min(14.0 / sw, 14.0 / sh)
        tw = max(1, int(round(sw * scale)))
        th = max(1, int(round(sh * scale)))
    
    # Downsample using BOX area averaging
    down = sprite.resize((tw, th), Image.Resampling.BOX)
    darr = np.array(down)
    
    # Clean binary alpha
    alpha = darr[:, :, 3] >= 95
    alpha = binary_fill_holes(alpha)
    alpha = remove_orphan_pixels(alpha)
    
    darr[~alpha] = 0
    darr[alpha, 3] = 255
    
    # Palette optimization & color quantization
    opaque = darr[alpha, :3].astype(float)
    lum = 0.299 * opaque[:, 0] + 0.587 * opaque[:, 1] + 0.114 * opaque[:, 2]
    mean_lum = lum.mean()
    
    # Contrast and saturation boost
    contrast_pixels = (opaque - mean_lum) * c_boost + mean_lum
    gray = np.tile(lum[:, None], (1, 3))
    sat_pixels = gray + (contrast_pixels - gray) * s_boost
    enhanced = np.clip(sat_pixels, 0, 255)
    
    # K-means clustering (8-13 colors for clean pixel art)
    if k is None:
        k = 9 if 'knife' in name else 12
    centroids, c_labels = kmeans2(enhanced, k, minit='points', iter=35)
    
    # Merge color centers that are too close
    merged_centroids = []
    mapping = {}
    for ci, c in enumerate(centroids):
        found = False
        for mi, mc in enumerate(merged_centroids):
            if np.linalg.norm(c - mc) < merge_dist:
                mapping[ci] = mi
                found = True
                break
        if not found:
            mapping[ci] = len(merged_centroids)
            merged_centroids.append(c.copy())
            
    merged_centroids = np.array(merged_centroids)
    new_labels = np.array([mapping[l] for l in c_labels])
    
    # Safety: Clamp minimum brightness of darkest shades to max(RGB) >= 56
    for mc in merged_centroids:
        if max(mc) < 56:
            mc[:] = mc * (56.0 / max(max(mc), 1.0))
            
    # Modal filter on color labels to eliminate dithering / orphan noise pixels
    label_map = np.zeros((th, tw), dtype=int) - 1
    label_map[alpha] = new_labels
    cleaned_labels = label_map.copy()
    
    for y in range(th):
        for x in range(tw):
            if not alpha[y, x]:
                continue
            neighbors = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < th and 0 <= nx < tw and alpha[ny, nx]:
                        neighbors.append(label_map[ny, nx])
            if len(neighbors) >= 5:
                vals, counts = np.unique(neighbors, return_counts=True)
                top_val = vals[np.argmax(counts)]
                if label_map[y, x] != top_val and counts.max() >= len(neighbors) - 2:
                    cleaned_labels[y, x] = top_val
                    
    darr[alpha, :3] = merged_centroids[cleaned_labels[alpha]].astype(np.uint8)
    
    # Crop tight bounding box
    d_alpha = darr[:, :, 3] > 0
    dy_idx, dx_idx = np.where(d_alpha)
    crop_x0, crop_y0 = int(dx_idx.min()), int(dy_idx.min())
    crop_x1, crop_y1 = int(dx_idx.max() + 1), int(dy_idx.max() + 1)
    cropped_darr = darr[crop_y0:crop_y1, crop_x0:crop_x1]
    cw, ch = crop_x1 - crop_x0, crop_y1 - crop_y0
    
    # Place and center inside 16x16 canvas
    res = np.zeros((16, 16, 4), dtype=np.uint8)
    off_x = (16 - cw) // 2
    off_y = (16 - ch) // 2
    res[off_y:off_y+ch, off_x:off_x+cw] = cropped_darr
    
    im_out = Image.fromarray(res)
    obbox = im_out.getbbox()
    pad = {'left': obbox[0], 'top': obbox[1], 'right': 16 - obbox[2], 'bottom': 16 - obbox[3]}
    
    # Fine-balance margins
    dx = (pad['right'] - pad['left']) // 2
    dy = (pad['bottom'] - pad['top']) // 2
    if dx != 0 or dy != 0:
        res = np.roll(res, (dy, dx), axis=(0, 1))
        im_out = Image.fromarray(res)
        obbox = im_out.getbbox()
        pad = {'left': obbox[0], 'top': obbox[1], 'right': 16 - obbox[2], 'bottom': 16 - obbox[3]}
        
    if name == 'dragon_skewer':
        # Reconstruct authentic continuous wooden skewer: connect tip at top-right and complete handle at bottom-left
        wood_light = np.array([255, 173, 24, 255], dtype=np.uint8)
        wood_dark = np.array([175, 95, 20, 255], dtype=np.uint8)
        wood_deep = np.array([125, 60, 15, 255], dtype=np.uint8)
        
        # 1. Top-right stick tip (connect through meat, remove isolated floating pixel)
        res[1, 13] = wood_light
        res[2, 12] = wood_light
        res[2, 13] = wood_dark
        res[3, 11] = wood_light
        res[3, 12] = wood_dark
        res[3, 13] = [0, 0, 0, 0]
        
        # 2. Bottom-left stick handle (fill handle down to row 14)
        res[12, 2] = wood_light
        res[13, 1] = wood_dark
        res[13, 2] = wood_light
        res[14, 1] = wood_deep
        res[14, 2] = wood_dark
        
        im_out = Image.fromarray(res)
        
    return im_out

def main():
    atlas = Image.open(ATLAS_PATH).convert('RGBA')
    ITEM_OUT.mkdir(parents=True, exist_ok=True)
    
    print(f"Loaded atlas: {ATLAS_PATH} ({atlas.size})")
    print(f"Optimizing all {len(NAMES)} item textures...")
    
    for idx, name in enumerate(NAMES):
        col, row = idx % 6, idx // 6
        if name == 'hunters_feast_serving':
            # Wide crop to capture the full platter that bled into the adjacent cell
            cell = atlas.crop((970, row * 256, (col + 1) * 256, (row + 1) * 256))
        else:
            cell = atlas.crop((col * 256, row * 256, (col + 1) * 256, (row + 1) * 256))
            
        optimized_im = optimize_texture(cell, name)
        dest = ITEM_OUT / f"{name}.png"
        optimized_im.save(dest)
        
        # Verify stats
        pixels = list(optimized_im.get_flattened_data())
        colors = len({p[:3] for p in pixels if p[3] > 0})
        near_black = sum(p[3] > 0 and max(p[:3]) < 55 for p in pixels)
        bbox = optimized_im.getbbox()
        print(f"  [{idx+1:2d}/{len(NAMES)}] {name:25s} -> bbox={bbox}, colors={colors:2d}, near_black={near_black}")
        
    if NETHER_ATLAS_PATH.exists():
        nether_atlas = Image.open(NETHER_ATLAS_PATH).convert('RGBA')
        print(f"\nLoaded nether atlas: {NETHER_ATLAS_PATH} ({nether_atlas.size})")
        print(f"Optimizing all {len(NETHER_ITEMS)} nether food textures...")
        for idx, (name, r, c, c_boost, s_boost, k, tw_th, merge_dist) in enumerate(NETHER_ITEMS):
            cell = nether_atlas.crop((c * 512, r * 512, (c + 1) * 512, (r + 1) * 512))
            optimized_im = optimize_texture(cell, name, tw_th=tw_th, c_boost=c_boost, s_boost=s_boost, k=k, merge_dist=merge_dist)
            dest = ITEM_OUT / f"{name}.png"
            optimized_im.save(dest)
            
            pixels = list(optimized_im.get_flattened_data())
            colors = len({p[:3] for p in pixels if p[3] > 0})
            near_black = sum(p[3] > 0 and max(p[:3]) < 55 for p in pixels)
            bbox = optimized_im.getbbox()
            print(f"  [{idx+1:2d}/{len(NETHER_ITEMS)}] {name:25s} -> bbox={bbox}, colors={colors:2d}, near_black={near_black}")

    print("\nAll textures exported successfully to:", ITEM_OUT)

if __name__ == '__main__':
    main()
