"""
Rebuild native 16x16 item and block textures from embedded pixel grids.
Legacy atlas optimization is retained for sprites without a handcrafted grid;
only that fallback requires the original atlases, NumPy and SciPy.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = ROOT / 'docs/generated-sprite-atlas.png'
NETHER_ATLAS_PATH = ROOT / 'docs/nether-food-atlas.png'
ITEM_OUT = ROOT / 'src/main/resources/assets/bossesrise_delight/textures/item'

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
    import numpy as np
    from scipy.ndimage import label

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
    import numpy as np
    from scipy.ndimage import label

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
    import numpy as np
    from scipy.ndimage import binary_fill_holes
    from scipy.cluster.vq import kmeans2

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

HANDCRAFTED_BOSS_STEWS = {
    'yeti_stew': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "N": "#24384a", "B": "#317a9e", "C": "#48c3e3", "I": "#98f4f4",
            "W": "#f4fbfb", "S": "#afd5e1", "R": "#682c36", "P": "#cc5a6b",
            "F": "#f5b0bc", "O": "#ff8e09", "E": "#c45108",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . N N N . . . .",
            ". . . . R R R . N W I C N . . .",
            ". . . R W F P R N I C B B N . .",
            ". . R W F P F P S W I C B N . .",
            ". . R F P F P W S I C B B N . .",
            ". . D P F P W W O E I C B D . .",
            ". K L W P W S O O E S C S L K .",
            ". K D D W S W O E S W S D D K .",
            ". K L D D S B D C I D D D D K .",
            ". . K L M M B M C M M M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'desert_stew': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "W": "#fcdd93", "T": "#c29d65", "A": "#945e36", "Z": "#604426",
            "R": "#8a2c06", "O": "#dc8218", "Y": "#f7bc5e", "G": "#6be11a",
            "V": "#39b430", "S": "#245c1c",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . K K K . . . .",
            ". . . . . . . . K W W T K . . .",
            ". . . . K K K . K Z W T A K . .",
            ". . . K W Y O K T A Z W T K . .",
            ". . . K Y O G G V T A Z T K . .",
            ". . D O R Y G V S W T A Z D . .",
            ". K L Y O R O Y O W T A O L K .",
            ". K D D O Y O R G V Y R D D K .",
            ". K L D D R D D G V D D D D K .",
            ". . K L M T A M V M A T D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'dragon_curry': (
        {
            "K": "#3a2414", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "Z": "#3c221e", "B": "#5e463e", "H": "#8c6e60", "R": "#7c1e08",
            "C": "#bd2f14", "O": "#e65c1c", "F": "#ff941c", "Y": "#ffd86b",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . Z Z Z . . .",
            ". . . . Z Z Z . . Z H Y H Z . .",
            ". . . Z C F C Z Z H Y F B Z . .",
            ". . Z C F Y C R B H F B Z . . .",
            ". . Z R C C R Y F B H B O Z . .",
            ". . D C R O F Y Y F B O C D . .",
            ". K L O C F Y Y F O C R C L K .",
            ". K D D O F Y F O C R O D D K .",
            ". K L D D R O F C R D D D D K .",
            ". . K L B M M O R M B M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'kraken_chowder': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "Z": "#3e1820", "R": "#9b2832", "C": "#e54953", "P": "#dda277",
            "S": "#f7ddc3", "W": "#fcfbed", "B": "#d4e0dc", "Y": "#eccd96",
            "G": "#4d8c3b", "E": "#265834",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . Z Z Z Z . . . .",
            ". . . . . . . Z C C C R Z . . .",
            ". . . . E E . Z S P C C R Z . .",
            ". . . E G G E Z Z S P C R Z . .",
            ". . E G G W Y W Z S P C R Z . .",
            ". . D G W B Y W S P C R W D . .",
            ". K L W B C R W S C R W B L K .",
            ". K D D W W B G W B Y W D D K .",
            ". K L D D W B G D D D D D D K .",
            ". . K L M M M B M M M M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'soul_braised_meat': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "A": "#57696b", "H": "#889c9b", "N": "#1e383e", "T": "#2c7f7c",
            "C": "#49e0d4", "W": "#bef9ff", "Z": "#442218", "G": "#5c3020",
            "B": "#784230", "R": "#9c5e44", "O": "#d36a0d", "Y": "#f2ab46",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . N N . . . .",
            ". . . . Z Z Z . . N C T N . . .",
            ". . . Z R R B Z N W C T N . . .",
            ". . Z R R B G B N W W C T N . .",
            ". . Z B R B G R C W C T B Z . .",
            ". . D B G B R O Y C T R B D . .",
            ". K H G B R O Y O C B R Y H K .",
            ". K D D O Y O G B T O Y D D K .",
            ". K H A D G D D C T D A H D K .",
            ". . K L M M M M T M M M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'sandworm_rice': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "W": "#fcfbed", "E": "#e6e2ce", "S": "#c4bfa4", "I": "#fcdd93",
            "T": "#d49848", "A": "#945e36", "Z": "#604426", "O": "#ff8e09",
            "R": "#b83c08", "G": "#6be11a", "V": "#39b430",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . K K K . . . . .",
            ". . . . . K K K I T A K . . . .",
            ". . . . K W W E Z I T A K . . .",
            ". . . K W W E W T Z I T A K . .",
            ". . K W E W S W G V T A Z K . .",
            ". . D E W O R W G V I T A D . .",
            ". K L W E O R W E S T A E L K .",
            ". K D D W E S W O E W S D D K .",
            ". K L D D S D D G V D D D D K .",
            ". . K L M T A M V M A T D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'sea_noodles': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "Z": "#3e1820", "R": "#9b2832", "C": "#e54953", "P": "#dda277",
            "S": "#f7ddc3", "Y": "#ffd86b", "N": "#e09c2c", "B": "#a66814",
            "G": "#4d8c3b", "E": "#265834", "A": "#48c3e3",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . Z Z Z Z . . . . . . .",
            ". . . . Z R C C S Z E E . . . .",
            ". . . Z R C C P S Z G E E . . .",
            ". . . Z R C P S P G G G E E . .",
            ". . D Z C P S Y Y N G E G D . .",
            ". . D Y Y C R N Y Y N G Y D . .",
            ". K L N Y Y N B N Y Y N B L K .",
            ". K D D N N B Y Y N B N D D K .",
            ". K L D D B D D A D D D D D K .",
            ". . K L M M M A M A M M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'soulfire_noodles': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "A": "#57696b", "H": "#889c9b", "N": "#1e383e", "T": "#2c7f7c",
            "C": "#49e0d4", "W": "#bef9ff", "Z": "#442218", "B": "#784230",
            "R": "#9c5e44", "E": "#bd2f14", "O": "#e67e1c", "Y": "#ffd86b",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . N N . . . . . . . .",
            ". . . . . N C T N . . . . . . .",
            ". . . . N W C T N Z Z Z . . . .",
            ". . . N W W C N Z R R B Z . . .",
            ". . D N C W C Y Y B R B E D . .",
            ". . D Y Y C T O Y Y B R E D . .",
            ". K H O Y Y O E O Y Y O E H K .",
            ". K D D O O E Y Y O E O D D K .",
            ". K H A D E D C T D D A H D K .",
            ". . K L M M M T M M M M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'yeti_dumplings': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "Z": "#5c4a38", "W": "#fcfbed", "E": "#e6e2ce", "S": "#c4bfa4",
            "N": "#24384a", "B": "#317a9e", "C": "#48c3e3", "I": "#98f4f4",
            "F": "#f29ca8", "G": "#6be11a", "V": "#39b430", "U": "#265834",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . N N N . . . .",
            ". . . . N N N . N I C B N . . .",
            ". . . N I C Z Z W W F E Z . . .",
            ". . Z W W F E Z W F W E S Z . .",
            ". U G Z W E S Z Z E S E S U . .",
            ". U G V Z W W F W E S S V G U .",
            ". K L G V W F W E S E V G L K .",
            ". K D D V S E W E S S V D D K .",
            ". K L D D D B C I B D D D D K .",
            ". . K L M M B M C M M M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'kraken_calamari': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "Z": "#3e1820", "R": "#9b2832", "C": "#e54953", "S": "#f7ddc3",
            "Y": "#ffd86b", "O": "#f09824", "B": "#b85c10", "W": "#fff688",
            "J": "#f0c410", "G": "#4d8c3b",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . Z Z Z . . . .",
            ". . . . K K K K Z C C R Z . . .",
            ". . . K Y Y O K Z S C R Z . . .",
            ". . K Y O R O Y K S C R Z . . .",
            ". . K Y O O Y Y O Y C R K . . .",
            ". . D B Y Y O R O Y W W J D . .",
            ". K L G B O Y O O B W J J L K .",
            ". K D D G B B O B G J J D D K .",
            ". K L D D G D D D D D D D D K .",
            ". . K L M M M M M M M M D K . .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'nightwatch_pie': (
        {
            "K": "#3c2214", "B": "#7c4218", "M": "#b06218", "O": "#e69628",
            "Y": "#ffd86b", "R": "#9c5e44", "G": "#5c2e1e", "A": "#57696b",
            "H": "#889c9b", "N": "#1e383e", "T": "#2c7f7c", "C": "#49e0d4",
            "W": "#bef9ff",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . N N . . . . . .",
            ". . . . K K K N C T N K . . . .",
            ". . . K Y Y O N W C T O K . . .",
            ". . K Y O Y H A W C A H O K . .",
            ". K Y O Y H A R C W C A O M K .",
            ". K O Y O Y R G T C T O Y M K .",
            ". K M O Y O G R C G O Y O M K .",
            ". K B G R C G O Y Y O M M B K .",
            ". . K B G R G B O O M B B K . .",
            ". . . K K B G K M M B K K . . .",
            ". . . . . K K . K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'frosted_berry_tart': (
        {
            "K": "#3c2414", "M": "#8c4c16", "O": "#d98224", "Y": "#ffd466",
            "N": "#24384a", "B": "#317a9e", "C": "#48c3e3", "I": "#98f4f4",
            "W": "#f4fbfb", "S": "#bfdee8", "Z": "#4a1620", "E": "#9b1c28",
            "R": "#e53945", "P": "#ff8a94", "G": "#4d8c3b",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . N N N . . . . .",
            ". . . . . Z Z N W I C N . . . .",
            ". . . . Z P R R I C B N . . . .",
            ". . . Z R R E G I C B Z Z . . .",
            ". . N I W R E G P R R P R Z . .",
            ". K Y W W S W W R E E R E Y K .",
            ". K Y W S I C W W S W S W O K .",
            ". K O Y W C B S I C S W O M K .",
            ". K M O Y B O Y C B O Y M M K .",
            ". . K M O M O M B O M O M K . .",
            ". . . K K M M O M O M K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'dragon_sandwich': (
        {
            "K": "#3c2214", "M": "#8e5218", "O": "#d98e2b", "Y": "#ffd86b",
            "B": "#5e463e", "H": "#8c6e60", "Z": "#3a1e1a", "R": "#7c1e08",
            "C": "#bd2f14", "F": "#ff781c", "G": "#6be11a", "V": "#39b430",
            "U": "#24581c",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . K K K K . . . . .",
            ". . . . . K K Y Y Y O K Z Z . .",
            ". . . K K Y Y Y O Y O Z H B Z .",
            ". . K Y Y O Y Y O O M O H B Z .",
            ". K Y O Y Y O O M M K C F R Z .",
            ". K M O O M M K K C F Y C R Z .",
            ". Z C F K K C F Y F C R C G U .",
            ". Z R C F Y F C R C R G V G U .",
            ". . U G V G C R G V G V O K . .",
            ". . K M G V G V O O O M K . . .",
            ". . . K K M O O M M K K . . . .",
            ". . . . . K K K K K . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'sandworm_wrap': (
        {
            "K": "#3a2610", "M": "#966220", "O": "#df9e38", "Y": "#fce694",
            "W": "#fcdd93", "T": "#c29d65", "A": "#945e36", "Z": "#604426",
            "R": "#8a2c06", "C": "#d44218", "G": "#6be11a", "V": "#39b430",
            "U": "#24581c",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . K K K K . . .",
            ". . . . . . . K K Y Y Y O K . .",
            ". . . . . K K Y Y Y O Z Y O K .",
            ". . . K K G V K Y Y Y Y O O K .",
            ". . K W W T G V K Y Z Y Y O K .",
            ". K W Z W T A G K Y Y O Y M K .",
            ". K T A Z W T C K Y O Z O M K .",
            ". K G T A Z C R V K Y O M K . .",
            ". . U G V C R G V O O M K . . .",
            ". . . U V G V K O O M K . . . .",
            ". . . . K K K M M K K . . . . .",
            ". . . . . . K K K . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'dragon_skewer': (
        {
            "K": "#3a2214", "D": "#683c16", "L": "#b87428", "Z": "#3c201c",
            "B": "#5e463e", "H": "#8c6e60", "R": "#7c1e08", "C": "#bd2f14",
            "O": "#e65c1c", "F": "#ff941c", "Y": "#ffd86b", "G": "#4d8c3b",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . Z Z .",
            ". . . . . . . . . . . . Z H B .",
            ". . . . . . . . Z Z Z Z H B Z .",
            ". . . . . . . Z C F Y C B Z . .",
            ". . . . . . Z C Y F O C R Z . .",
            ". . . . . . Z R C F C R Z . . .",
            ". . . . . Z H B Z R G G Z . . .",
            ". . . Z Z B H H B G G Z . . . .",
            ". . Z C F C B R C F R Z . . . .",
            ". . Z C Y F C F Y F R Z . . . .",
            ". . Z R C F O C R R Z . . . . .",
            ". K L Z Z R R R Z Z . . . . . .",
            ". K D L K Z Z Z . . . . . . . .",
            ". . K K . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'hunters_feast_serving': (
        {
            "K": "#3a2610", "D": "#533909", "M": "#714f0f", "L": "#926c3e",
            "Z": "#3e1820", "R": "#881e24", "C": "#d9382e", "F": "#ff881c",
            "Y": "#ffd86b", "N": "#24384a", "B": "#317a9e", "A": "#48c3e3",
            "I": "#98f4f4", "S": "#f7ddc3", "T": "#b87c38", "G": "#6be11a",
            "V": "#39b430",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . N N N . . . . . .",
            ". . . . Z Z N I A B N Z Z . . .",
            ". . . Z C F Z I A B Z C R Z . .",
            ". . Z C Y F C I A Z S C C R Z .",
            ". . Z R C F C S Y T S T C R Z .",
            ". . D G R C S Y T D S Y T R D .",
            ". K L G V R S Y T D S T G L K .",
            ". K D D G V G V T G V G D D K .",
            ". K L D D V D D A D D V D D K .",
            ". . K L M M M B M T M M M D K .",
            ". . . K K D M M M M D K K . . .",
            ". . . . . K K K K K K . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'kraken_hotpot_serving': (
        {
            "K": "#262e38", "D": "#36424c", "A": "#576972", "H": "#889ca4",
            "Z": "#3e1820", "R": "#9b2832", "C": "#e54953", "P": "#dda277",
            "S": "#f7ddc3", "W": "#fcfbed", "Y": "#ffd86b", "O": "#ff821c",
            "G": "#4d8c3b", "B": "#317a9e", "I": "#78ecf4",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . Z Z Z . . Z Z Z . . . .",
            ". . . Z R C C Z Z C C R Z . . .",
            ". . Z R C P S Z I Z S P C Z . .",
            ". . Z R C S W Y B Y S C R Z . .",
            ". . K H C S W O Y G W S C H K .",
            ". K H D W Y O W G Y O W Y D K .",
            ". K D H W Y O W Y O W G H D K .",
            ". . K D H H H I B I H H D K . .",
            ". . K H A A D B I B D A A D K .",
            ". . . K H A A A B A A A D K . .",
            ". . . . K K D A A A D K K . . .",
            ". . . . . K K . . . K K . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'raw_dragon_cut': (
        {
            "Z": "#3a1e22", "K": "#563238", "B": "#6e544a", "H": "#9c8274",
            "W": "#dfd0c4", "D": "#7c1420", "R": "#b81e30", "C": "#e6384c",
            "P": "#ff7a8a", "O": "#ff781c", "Y": "#ffd86b",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . Z Z . Z Z . .",
            ". . . . . . . . Z W H Z H B Z .",
            ". . . . . . . . Z H Y H B B Z .",
            ". . . . . Z Z Z Z B H O B Z . .",
            ". . . Z Z K K C P C B H Z . . .",
            ". . Z K K C C P Y O C R Z Z . .",
            ". Z K C C P C O Y O C P C D Z .",
            ". Z K C P R C R O C P C R D Z .",
            ". Z K C R D R C C P C R R D Z .",
            ". Z K R D R C P C R R D D Z . .",
            ". . Z R R C P C R D D Z Z . . .",
            ". . . Z D R C R D Z Z . . . . .",
            ". . . . Z Z D D Z . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'raw_yeti_cut': (
        {
            "N": "#24384a", "B": "#317a9e", "C": "#48c3e3", "I": "#98f4f4",
            "W": "#f4fbfb", "S": "#cfe8f0", "Z": "#5c2230", "D": "#8e3446",
            "R": "#c85268", "P": "#ee889a", "F": "#f9c4ce",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . N N N N . . . .",
            ". . . . . N N N W I I C N . . .",
            ". . . . N W I C S W I C B N . .",
            ". . . Z W S C B P W S C B N . .",
            ". . Z W F P P W F P P W B N . .",
            ". Z W F P R P W F R P W S Z . .",
            ". Z F P R D W F P R D W F R Z .",
            ". Z P R D P W F R D W F R D Z .",
            ". . Z R P F W R D W F R D Z . .",
            ". . . Z R F P R D R D D Z . . .",
            ". . . . Z D R R D D Z Z . . . .",
            ". . . . . Z Z Z Z Z . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'raw_sandworm_fillet': (
        {
            "K": "#3c2012", "Z": "#604426", "A": "#945e36", "T": "#c29d65",
            "W": "#fcdd93", "R": "#942e0c", "O": "#d96220", "F": "#ff9c40",
            "U": "#224e18", "V": "#39b430", "G": "#6be11a",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . K K K K . . .",
            ". . . . . . . K K W T A Z K . .",
            ". . . . . K K W T Z W T A K . .",
            ". . . . K W T A F O Z T A K . .",
            ". . . K W Z A F F O R A Z K . .",
            ". . K W T A F O R G V O A K . .",
            ". K W T Z F O R G G V R K . . .",
            ". K T A F W F O G V V U U . . .",
            ". K A F W F O R G V U . . . . .",
            ". . K O F O R G V U . . . . . .",
            ". . . K R R G V U . . . . . . .",
            ". . . . K U U U . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'raw_kraken_tentacle': (
        {
            "Z": "#3e1620", "D": "#6e1c24", "R": "#a42832", "C": "#ce3741",
            "L": "#e54953", "M": "#ff7882", "A": "#b86844", "P": "#dda277",
            "S": "#f7ddc3",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . Z Z Z Z . . . . .",
            ". . . . . . Z M L L C Z . . . .",
            ". . . . . Z M L C C R C Z . . .",
            ". . . . . Z L C Z S P C R Z . .",
            ". . . . . . Z Z Z P S P C R Z .",
            ". . . . . . . . Z S P C L R Z .",
            ". . . . . . . . Z P S P L R Z .",
            ". . . Z Z Z . Z S P A C L R Z .",
            ". . Z L M L Z S S A C L C R Z .",
            ". . Z L C C S P A P C L R D Z .",
            ". . Z R C L C S S C L R D Z . .",
            ". . . Z R L C C L R D D Z . . .",
            ". . . . Z D R R D D Z Z . . . .",
            ". . . . . Z Z Z Z Z . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'roasted_dragon_cut': (
        {
            "Z": "#3c1c14", "K": "#5c2818", "B": "#78523e", "H": "#a88268",
            "W": "#e4ceb8", "D": "#843016", "R": "#b84a1c", "C": "#df7428",
            "P": "#f6a246", "O": "#ff8818", "Y": "#ffe270",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . Z Z . Z Z . .",
            ". . . . . . . . Z W H Z H B Z .",
            ". . . . . . . . Z H Y H B B Z .",
            ". . . . . Z Z Z Z B H O B Z . .",
            ". . . Z Z K K C P C B H Z . . .",
            ". . Z K K C K D Y O C R Z Z . .",
            ". Z K C P C R K O Y O P C D Z .",
            ". Z K P K D C P K O C K R D Z .",
            ". Z K C R K D C P K C R K D Z .",
            ". Z K R D R K D C P K R D Z . .",
            ". . Z R R C P K D R D Z Z . . .",
            ". . . Z D R C R D Z Z . . . . .",
            ". . . . Z Z D D Z . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'cooked_yeti_cut': (
        {
            "N": "#24384a", "B": "#317a9e", "C": "#48c3e3", "I": "#98f4f4",
            "W": "#fff6e4", "S": "#d8eef4", "Z": "#442212", "D": "#743a1c",
            "R": "#a85c2a", "P": "#d88a44", "F": "#f6c276",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . N N N N . . . .",
            ". . . . . N N N W I I C N . . .",
            ". . . . N W I C S I C B N . . .",
            ". . . Z W S C B P W S C B N . .",
            ". . Z W F P P W F P P W B N . .",
            ". Z W F D P R W F D P W S Z . .",
            ". Z F P R D W F P R D W F R Z .",
            ". Z P R D P W F R D W F R D Z .",
            ". . Z R P F W R D W F R D Z . .",
            ". . . Z R F P R D R D D Z . . .",
            ". . . . Z D R R D D Z Z . . . .",
            ". . . . . Z Z Z Z Z . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'purified_sandworm_fillet': (
        {
            "K": "#3c2212", "Z": "#644424", "A": "#986236", "T": "#c69e62",
            "W": "#fcdf96", "R": "#9e4818", "O": "#d87c28", "F": "#f6ae48",
            "H": "#ffe8a6", "M": "#48a898", "S": "#aef6ec",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . K K K K . . .",
            ". . . . . . . K K W T A Z K . .",
            ". . . . . K K W T Z W T A K . .",
            ". . . . K W T A H F Z T A K . .",
            ". . . K W Z A H H F R A Z K . .",
            ". . K W T A F R H F O S M K . .",
            ". K W T Z H F O R H O S M . . .",
            ". K T A H W H F O R S M . . . .",
            ". K A H W H F O S M K . . . . .",
            ". . K O H F O S M K . . . . . .",
            ". . . K R O R K K . . . . . . .",
            ". . . . K K K . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'grilled_kraken_tentacle': (
        {
            "Z": "#3c1814", "D": "#682018", "R": "#9e301c", "C": "#cc4a22",
            "L": "#ee7228", "M": "#ffb448", "A": "#9e5024", "P": "#d68442",
            "S": "#f8dc8c", "W": "#fff4cc",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . Z Z Z Z . . . . .",
            ". . . . . . Z M L C D Z . . . .",
            ". . . . . Z M L C D R C Z . . .",
            ". . . . . Z L C Z W P C R Z . .",
            ". . . . . . Z Z Z P S P D D Z .",
            ". . . . . . . . Z S P C L R Z .",
            ". . . . . . . . Z P W P L R Z .",
            ". . . Z Z Z . Z S P A D D D Z .",
            ". . Z L M L Z W S A C L C R Z .",
            ". . Z L C D S P A P C L R D Z .",
            ". . Z R D L C W S C D R D Z . .",
            ". . . Z R L C C L D D D Z . . .",
            ". . . . Z D R R D D Z Z . . . .",
            ". . . . . Z Z Z Z Z . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'nether_ember': (
        {
            "Z": "#24343a", "D": "#384a52", "M": "#57696b", "L": "#889c9b",
            "U": "#1c5264", "B": "#2288a8", "C": "#47dfe5", "S": "#9efcff",
            "W": "#ffffff",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . Z Z C Z . . . . . .",
            ". . . . . Z L M S C Z . . . . .",
            ". . . . Z L M C W S M Z . . . .",
            ". . . . Z M B S W C D Z . . . .",
            ". . . . . Z D B C B Z Z Z . . .",
            ". . . Z Z Z Z U C U Z L M Z . .",
            ". . Z L M D Z C S C D M L D Z .",
            ". Z L M C B Z B W S B C M D Z .",
            ". Z M B S W C D B C S W C D Z .",
            ". Z D B W S B Z Z B S W C D Z .",
            ". . Z D C B Z . . Z D C B Z . .",
            ". . . Z Z Z . . . . Z Z Z . . .",
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'soul_salt': (
        {
            "K": "#3a2618", "N": "#624028", "A": "#8e6240", "T": "#bc8e62",
            "P": "#e4be92", "Z": "#26363c", "M": "#57696b", "L": "#96acab",
            "B": "#24869e", "C": "#47dfe5", "S": "#a6fcff", "W": "#ffffff",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . K K K K . . . . . .",
            ". . . . . K T S W C K K . . . .",
            ". . . . K P S W C S W C K . . .",
            ". . . K T B C S W S C B T K . .",
            ". . . K A B S W C B C S A K . .",
            ". . . . Z M L M C M L M Z . . .",
            ". . . . Z Z M M L M M Z Z . . .",
            ". . . K N A Z Z Z Z Z A N K . .",
            ". . K T P T A A N A A T A N K .",
            ". . K T P P T A A B C A A N K .",
            ". . K A T P T A B S C A N N K .",
            ". . K N A T A A A B A N N K . .",
            ". . . K N N A A A N N N K . . .",
            ". . . . K K K K K K K K . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'dragonbone_knife': (
        {
            "Z": "#3a241e", "D": "#54382e", "B": "#74584c", "H": "#9e8272",
            "P": "#cbb4a2", "W": "#f4e8dc", "K": "#64181e", "R": "#a42422",
            "C": "#e23c34", "O": "#ff781c", "Y": "#ffd86b",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . Z Z Z . .",
            ". . . . . . . . . . Z D H W Z .",
            ". . . . . . . . . Z D O P W Z .",
            ". . . . . . . . Z D Y O P W Z .",
            ". . . . . . . Z B O Y H P W Z .",
            ". . . . . . Z D Y O H P W Z . .",
            ". . . . . Z B O Y H P P W Z . .",
            ". . . . Z H R O H P P W Z . . .",
            ". . . K C R Z H B P W Z . . . .",
            ". . K C R K . Z B W Z . . . . .",
            ". Z H C R K . . Z Z . . . . . .",
            ". Z W H K Z . . . . . . . . . .",
            ". . Z H W Z . . . . . . . . . .",
            ". . . Z Z . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
    'krakentooth_knife': (
        {
            "Z": "#382220", "D": "#4e322a", "B": "#684638", "R": "#873636",
            "C": "#b74d62", "L": "#e55b6d", "P": "#d8aa8e", "W": "#f7e2cc",
            "G": "#243a44", "T": "#3c6270", "O": "#f99717",
        },
        [
            ". . . . . . . . . . . . . . . .",
            ". . . . . . . . . . . Z Z Z . .",
            ". . . . . . . . . . Z D P W Z .",
            ". . . . . . . . . Z D C P W Z .",
            ". . . . . . . . Z D B L P W Z .",
            ". . . . . . . Z B C L P P W Z .",
            ". . . . . . Z D B L C P W Z . .",
            ". . . . . Z B C L C P P W Z . .",
            ". . . . Z C O R C P P W Z . . .",
            ". . . G T G Z R C P W Z . . . .",
            ". . G T G G . Z R W Z . . . . .",
            ". Z L T G G . . Z Z . . . . . .",
            ". Z W L G Z . . . . . . . . . .",
            ". . Z L W Z . . . . . . . . . .",
            ". . . Z Z . . . . . . . . . . .",
            ". . . . . . . . . . . . . . . .",
        ],
    ),
}

HANDCRAFTED_BLOCK_TEXTURES = {
    'roast': (
        {
            "Z": "#3c2016", "D": "#74361c", "R": "#b44a20", "O": "#e07828",
            "F": "#f6ae48", "Y": "#ffe270", "W": "#fff6e4", "T": "#c69e62",
            "B": "#317a9e", "C": "#48c3e3", "I": "#98f4f4", "U": "#265820",
            "G": "#4eb834",
        },
        [
            "Z T W T Z R D Z Z B C I I C B Z",
            "T W Y T R O R D B C I W I C F Z",
            "Z T O R D Z O R C I W F W F O Z",
            "D R O Y O R Z D Z W F O D F W Z",
            "R O Z Y O R D R D F O D F W F D",
            "O R D Z O R Z D Z O D F W F O D",
            "R D R O Z D R D D F W F O D F Z",
            "Z D R D R D Z Z Z Z D F O D Z Z",
            "Z Z T W T Z T Z Z D R O R D U G",
            "Z T W T Z T W T D R W Y R O G U",
            "T W T Z F Y F Z R O Y W R D U G",
            "Z T F Y W F O R O R D R W Y G G",
            "T Z F W F O R D R W Y R Y W R U",
            "W T O F O R F O D Y W R D R O G",
            "T Z R O R F W F Z D R O R D U G",
            "Z Z Z D R O F Z U G U Z D U G U",
        ],
    ),
    'metal': (
        {
            "Z": "#28363c", "D": "#38464c", "M": "#52646a", "L": "#788c92",
            "S": "#a4b8be", "A": "#8e5822", "B": "#c88632", "G": "#f6c668",
            "R": "#9e241c", "O": "#ff781c", "Y": "#ffe270",
        },
        [
            "D L S S L D L S S L D L S S L D",
            "Z M L L M Z M L L M Z M L L M Z",
            "D B G B A D B G B A D B G B A D",
            "Z Z D D Z Z Z D D Z Z Z D D Z Z",
            "D M L M D D M L M D D M L M D Z",
            "D M L M D D M B G B M L M D D Z",
            "D M L M D D B G Y G B L M D D Z",
            "D M L M D D M B G B M L M D D Z",
            "D M L M D D M L M D D M L M D Z",
            "Z D M D Z Z D M D Z Z D M D Z Z",
            "D A B G B A B G B A B G B A B D",
            "Z Z D D Z Z Z D D Z Z Z D D Z Z",
            "Z D R O Y O R D Z D R O Y O R Z",
            "Z R O Y Y O R D Z R O Y Y O R Z",
            "Z D R O O R D Z Z D R O O R D Z",
            "Z Z Z D D Z Z Z Z Z Z D D Z Z Z",
        ],
    ),
    'broth': (
        {
            "Z": "#38464c", "M": "#788c92", "D": "#8e1c22", "R": "#c82c28",
            "O": "#f26422", "Y": "#ffd258", "A": "#c89654", "P": "#ecc682",
            "W": "#fff6dc", "C": "#58cce6", "G": "#4eb834",
        },
        [
            "D R R O R D R Z M A P W P A P A",
            "R O Y O R R D Z M P W C W P A P",
            "R Y O R D G R Z M W C W P G P W",
            "O R R D R R O Z M P W P A P W P",
            "R D R O Y O R Z M A P Y P W P A",
            "D R O Y O R D Z M P Y W P A G P",
            "R G R O R D R Z M W P A P W P W",
            "R R D R O R D Z M P A G P W C W",
            "O R R O Y O R Z M A P W P C W P",
            "R O Y O R D R Z M P W C W P A P",
            "D R O R D G R Z M W C W P Y P A",
            "R D R R O R O Z M P W P Y W P W",
            "R O Y O R D R Z M A P G P W P A",
            "O Y O R G R D Z M P G A P A P W",
            "R O R D R O R Z M W P W P W P A",
            "D R D R R D R Z M A P A P A P A",
        ],
    ),
    'tentacle': (
        {
            "Z": "#3e1820", "D": "#7a2028", "R": "#b82e38", "L": "#e84c56",
            "P": "#dfa478", "S": "#f8dec4", "W": "#fff8ea", "O": "#e07828",
            "Y": "#ffd258", "B": "#6e4628", "U": "#224e18", "G": "#48b430",
        },
        [
            "Z D R L L R D Z Z O Y Y O O Y Z",
            "D R L L R P S D O Y W W Y O L O",
            "R L R D P S W S Y W O O W Y O L",
            "L R D S W S P R Y O L L O Y L O",
            "L R P S P R L L O Y W W Y O L O",
            "R D S W S D R L Y O Y Y O L O Y",
            "D R P S P R D Z O L O O L O Y Z",
            "Z D R R D Z Z Z Z O Y Y O Z Z Z",
            "Z S W W S Z B Z U G G U O O U G",
            "S W W W S B P B G U U G O Y G U",
            "W W S W S B B Z G U G G U O U G",
            "S W W W S Z P Z U G G U G U G G",
            "Z S S S Z B B B G U U G O O U G",
            "B B P B Z B P B U G G U O Y G U",
            "B P W P B B B Z G U G U U O U G",
            "Z B B B Z Z Z Z U G U G G U G U",
        ],
    ),
}

def render_handcrafted(palette, grid):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(grid):
        for x, tok in enumerate(row.split()):
            if tok != ".":
                hx = palette[tok].lstrip("#")
                im.putpixel((x, y), (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16), 255))
    return im

def main():
    atlas = None
    ITEM_OUT.mkdir(parents=True, exist_ok=True)

    print(f"Rebuilding all {len(NAMES)} item textures...")

    for idx, name in enumerate(NAMES):
        if name in HANDCRAFTED_BOSS_STEWS:
            optimized_im = render_handcrafted(*HANDCRAFTED_BOSS_STEWS[name])
        else:
            if atlas is None:
                atlas = Image.open(ATLAS_PATH).convert('RGBA')
            col, row = idx % 6, idx // 6
            if name == 'hunters_feast_serving':
                # Wide crop to capture the full platter that bled into the adjacent cell.
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

    nether_atlas = None
    print(f"\nRebuilding all {len(NETHER_ITEMS)} nether food textures...")
    for idx, (name, r, c, c_boost, s_boost, k, tw_th, merge_dist) in enumerate(NETHER_ITEMS):
        if name in HANDCRAFTED_BOSS_STEWS:
            optimized_im = render_handcrafted(*HANDCRAFTED_BOSS_STEWS[name])
        else:
            if nether_atlas is None:
                nether_atlas = Image.open(NETHER_ATLAS_PATH).convert('RGBA')
            cell = nether_atlas.crop((c * 512, r * 512, (c + 1) * 512, (r + 1) * 512))
            optimized_im = optimize_texture(cell, name, tw_th=tw_th, c_boost=c_boost, s_boost=s_boost, k=k, merge_dist=merge_dist)
        dest = ITEM_OUT / f"{name}.png"
        optimized_im.save(dest)

        pixels = list(optimized_im.get_flattened_data())
        colors = len({p[:3] for p in pixels if p[3] > 0})
        near_black = sum(p[3] > 0 and max(p[:3]) < 55 for p in pixels)
        bbox = optimized_im.getbbox()
        print(f"  [{idx+1:2d}/{len(NETHER_ITEMS)}] {name:25s} -> bbox={bbox}, colors={colors:2d}, near_black={near_black}")

    block_out = ITEM_OUT.parent / 'block'
    block_out.mkdir(parents=True, exist_ok=True)
    for name, (pal, grid) in HANDCRAFTED_BLOCK_TEXTURES.items():
        block_im = render_handcrafted(pal, grid)
        block_im.save(block_out / f"{name}.png")

    print("\nAll item and block textures exported successfully to:", ITEM_OUT)

if __name__ == '__main__':
    main()
