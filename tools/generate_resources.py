"""Rebuild recipes, models, localization and Java item declarations from the food catalogue."""
from pathlib import Path
import json
import gzip
import struct
from culinary_catalogue import EFFECTS, MEAL_PROFILES, NETHER_FOODS, SEASONINGS

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'src/main/resources'
MOD = 'bossesrise_delight'

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def item(name):
    return name if ':' in name else f'{MOD}:{name}'

def ingredient(name):
    return {'tag': name[1:]} if name.startswith('#') else {'item': item(name)}

# id, English, Chinese, nutrition, saturation, bowl, effects (id, seconds, chance), note
FOODS = [
    ('raw_dragon_cut', 'Raw Dragon Cut', '生龙肉排', 4, .3, False, [('hunger', 20, .3)], 'dragon_source'),
    ('raw_yeti_cut', 'Raw Yeti Cut', '生雪怪肉', 3, .3, False, [('hunger', 20, .3)], 'yeti_source'),
    ('raw_sandworm_fillet', 'Raw Sandworm Fillet', '生沙虫肉段', 3, .2, False, [('poison', 12, 1)], 'worm_source'),
    ('raw_kraken_tentacle', 'Raw Kraken Tentacle', '生克拉肯触手', 3, .3, False, [('hunger', 20, .3)], 'kraken_source'),
    ('roasted_dragon_cut', 'Roasted Dragon Cut', '烤龙肉排', 8, .8, False, [], None),
    ('cooked_yeti_cut', 'Cooked Yeti Cut', '熟雪怪肉', 7, .7, False, [], None),
    ('purified_sandworm_fillet', 'Cleaned Sandworm Fillet', '净化沙虫肉', 3, .4, False, [], 'cleaned_worm'),
    ('grilled_kraken_tentacle', 'Grilled Kraken Tentacle', '烤克拉肯触手', 7, .7, False, [], None),
    ('dragon_skewer', 'Dragon Skewer', '龙肉烤串', 8, .8, False, [], None),
    ('dragon_curry', 'Dragonfire Curry', '龙焰咖喱', 10, .8, True, [], None),
    ('dragon_sandwich', 'Dragon Cut Sandwich', '龙肉三明治', 9, .8, False, [], None),
    ('yeti_stew', 'Snowfield Yeti Stew', '雪原雪怪炖汤', 10, .8, True, [], None),
    ('yeti_dumplings', 'Yeti Dumplings', '雪怪肉饺', 8, .8, True, [], None),
    ('frosted_berry_tart', 'Frosted Berry Tart', '霜糖莓果挞', 6, .6, False, [], None),
    ('sandworm_wrap', 'Sandworm Flatbread Wrap', '沙虫卷饼', 9, .7, False, [], None),
    ('desert_stew', 'Desert Hunter Stew', '沙漠猎人炖汤', 10, .8, True, [], None),
    ('sandworm_rice', 'Sandworm Rice Bowl', '沙虫盖饭', 10, .8, True, [], None),
    ('kraken_calamari', 'Kraken Calamari', '香炸克拉肯圈', 8, .8, True, [], None),
    ('kraken_chowder', 'Kraken Chowder', '克拉肯浓汤', 10, .8, True, [], None),
    ('sea_noodles', 'Deep Sea Noodles', '深海触手面', 10, .8, True, [], None),
    ('hunters_feast_serving', "Hunter's Feast Serving", '猎人盛宴拼盘', 12, .9, True, [], None),
    ('kraken_hotpot_serving', 'Kraken Hotpot Serving', '克拉肯海鲜火锅碗', 12, .9, True, [], None),
]
FOODS = [row[:6] + (MEAL_PROFILES.get(row[0], row[6]), row[7]) for row in FOODS] + NETHER_FOODS

def recipe(path, value):
    write(RES / f'data/{MOD}/recipe/{path}.json', value)

def cooking(name, inputs, count=1, bowl=True):
    value = {'type': 'farmersdelight:cooking', 'ingredients': [ingredient(n) for n in inputs],
             'result': {'id': item(name), 'count': count}, 'cookingtime': 200,
             'experience': 1.0, 'recipe_book_tab': 'meals' if bowl else 'misc'}
    if bowl: value['container'] = {'id': 'minecraft:bowl', 'count': 1}
    recipe('cooking/' + name, value)

def shapeless(name, inputs, count=1):
    recipe('crafting/' + name, {'type': 'minecraft:crafting_shapeless', 'category': 'misc',
                              'ingredients': [ingredient(n) for n in inputs], 'result': {'id': item(name), 'count': count}})

def cutting(name, source, result, count=1):
    recipe('cutting/' + name, {'type': 'farmersdelight:cutting', 'ingredients': [ingredient(source)],
                            'tool': {'type': 'farmersdelight:item_ability', 'action': 'knife_dig'},
                            'result': [{'item': {'id': item(result), 'count': count}}]})

def box_uv(start, end, face_map):
    faces = {}
    for side in ['north', 'south', 'west', 'east', 'up', 'down']:
        if side in face_map:
            tex, uv = face_map[side][:2]
            entry = {'uv': uv, 'texture': tex}
            if len(face_map[side]) > 2:
                entry.update(face_map[side][2])
            faces[side] = entry
    return {'from': start, 'to': end, 'faces': faces}

def uniform_box(start, end, texture, uv=None, top_tex=None, top_uv=None, side_uv=None, down_tex=None):
    u = uv or [0, 0, 16, 16]
    su = side_uv or u
    tu = top_uv or u
    t_up = top_tex or texture
    t_down = down_tex or texture
    return box_uv(start, end, {
        'north': (texture, su), 'south': (texture, su),
        'west': (texture, su), 'east': (texture, su),
        'up': (t_up, tu), 'down': (t_down, u),
    })

FEAST_DISPLAY = {
    'gui': {'rotation': [30, 225, 0], 'translation': [0, 2.25, 0], 'scale': [0.82, 0.82, 0.82]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.4, 0.4, 0.4]},
    'fixed': {'rotation': [-90, 0, 0], 'translation': [0, 0, -4], 'scale': [0.75, 0.75, 0.75]},
    'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 2], 'scale': [0.5, 0.5, 0.5]},
    'thirdperson_lefthand': {'rotation': [75, 225, 0], 'translation': [0, 2.5, 2], 'scale': [0.5, 0.5, 0.5]},
    'firstperson_righthand': {'rotation': [0, 45, 0], 'translation': [0, 3.2, 0], 'scale': [0.55, 0.55, 0.55]},
    'firstperson_lefthand': {'rotation': [0, 225, 0], 'translation': [0, 3.2, 0], 'scale': [0.55, 0.55, 0.55]},
}

def feast_models(name, hotpot=False):
    variants = {}
    for servings in range(5):
        elements = []
        if hotpot:
            # 1. Glowing Brazier Stove Core & 4 Forged Iron Corner Feet (y=0..1)
            elements.append(uniform_box([3, 0, 3], [13, 1, 13], '#metal', uv=[2, 4, 14, 10], side_uv=[0, 12, 16, 16]))
            for fx, fz in [(2, 2), (12, 2), (2, 12), (12, 12)]:
                elements.append(uniform_box([fx, 0, fz], [fx + 2, 1, fz + 2], '#metal', uv=[0, 0, 4, 4], side_uv=[0, 2, 4, 4]))
            # 2. Cauldron Floor (y=1..2) & 4 Riveted Dark-Iron Walls (y=2..5)
            elements.append(uniform_box([2, 1, 2], [14, 2, 14], '#metal', uv=[2, 4, 14, 10], side_uv=[0, 10, 16, 12]))
            elements.append(uniform_box([2, 2, 2], [14, 5, 3], '#metal', uv=[0, 0, 16, 2], top_uv=[0, 0, 16, 2], side_uv=[0, 2, 16, 11]))
            elements.append(uniform_box([2, 2, 13], [14, 5, 14], '#metal', uv=[0, 0, 16, 2], top_uv=[0, 0, 16, 2], side_uv=[0, 2, 16, 11]))
            elements.append(uniform_box([2, 2, 3], [3, 5, 13], '#metal', uv=[0, 0, 16, 2], top_uv=[0, 0, 2, 16], side_uv=[0, 2, 16, 11]))
            elements.append(uniform_box([13, 2, 3], [14, 5, 13], '#metal', uv=[0, 0, 16, 2], top_uv=[14, 0, 16, 16], side_uv=[0, 2, 16, 11]))
            # 3. Central Yuanyang Hotpot Divider & 2 Ornate Brass Side Handles
            elements.append(uniform_box([7.5, 2, 3], [8.5, 4.3, 13], '#metal', uv=[7, 0, 9, 10], top_uv=[7, 0, 9, 16], side_uv=[0, 0, 16, 3]))
            elements.append(uniform_box([0, 2.5, 5.5], [2, 4.2, 10.5], '#metal', uv=[0, 10, 8, 12], side_uv=[0, 10, 12, 12]))
            elements.append(uniform_box([14, 2.5, 5.5], [16, 4.2, 10.5], '#metal', uv=[8, 10, 16, 12], side_uv=[4, 10, 16, 12]))
            # 4. Boiling Dual-Flavor Broth & 4 Sculpted Seafood Portions
            if servings > 0:
                elements.append(uniform_box([3, 2, 3], [13, 3.6, 13], '#broth', uv=[0, 0, 16, 16], side_uv=[0, 4, 16, 8]))
            hotpot_portions = [
                # Portion 1 (NW): Coiled Giant Kraken Tentacle Arch in Spicy Broth
                [
                    uniform_box([3.4, 3.4, 3.4], [7.4, 4.8, 7.4], '#food', uv=[0, 0, 8, 8], side_uv=[0, 1, 8, 6]),
                    uniform_box([4.0, 4.8, 4.0], [6.5, 5.8, 6.5], '#food', uv=[1, 1, 7, 7], side_uv=[1, 1, 7, 5]),
                ],
                # Portion 2 (NE): Crispy Golden Calamari & Seared Salmon in Creamy Broth
                [
                    uniform_box([8.6, 3.4, 3.4], [12.6, 4.8, 7.4], '#food', uv=[8, 0, 16, 8], side_uv=[8, 1, 16, 6]),
                    uniform_box([9.3, 4.8, 4.2], [11.8, 5.5, 6.7], '#food', uv=[9, 1, 15, 7], side_uv=[9, 1, 15, 5]),
                ],
                # Portion 3 (SW): Simmered Cod Tofu Cubes & Brown Mushrooms
                [
                    uniform_box([3.4, 3.4, 8.6], [7.4, 4.7, 12.6], '#food', uv=[0, 8, 8, 16], side_uv=[0, 9, 8, 15]),
                    uniform_box([4.2, 4.7, 9.4], [6.7, 5.4, 11.9], '#food', uv=[0, 8, 6, 14], side_uv=[1, 9, 7, 13]),
                ],
                # Portion 4 (SE): Second Coiled Kraken Tentacle & Deep-Sea Kelp
                [
                    uniform_box([8.6, 3.4, 8.6], [12.6, 4.8, 12.6], '#food', uv=[8, 8, 16, 16], side_uv=[0, 0, 8, 6]),
                    uniform_box([9.4, 4.8, 9.4], [11.9, 5.8, 11.9], '#food', uv=[1, 1, 7, 7], side_uv=[1, 1, 7, 5]),
                ],
            ]
            for grp in hotpot_portions[:servings]:
                elements.extend(grp)
        else:
            # 1. Rimmed Wooden Feast Platter (y=0..2) using proportional Farmer's Delight tray UVs
            elements.append(uniform_box([2, 0, 2], [14, 1, 14], '#tray', uv=[2, 2, 14, 14], side_uv=[2, 15, 14, 16], down_tex='#tray_bottom'))
            elements.append(uniform_box([2, 1, 2], [14, 2, 3], '#tray', uv=[2, 1, 14, 2], side_uv=[2, 14, 14, 15]))
            elements.append(uniform_box([2, 1, 13], [14, 2, 14], '#tray', uv=[2, 14, 14, 15], side_uv=[2, 14, 14, 15]))
            elements.append(uniform_box([2, 1, 3], [3, 2, 13], '#tray', uv=[1, 3, 2, 13], side_uv=[3, 14, 13, 15]))
            elements.append(uniform_box([13, 1, 3], [14, 2, 13], '#tray', uv=[14, 3, 15, 13], side_uv=[3, 14, 13, 15]))
            if servings == 0:
                # Leftover gnawed Dragon Bone & Frost Crystal shard on the tray
                elements.append(uniform_box([4.5, 1, 5], [9.5, 2, 7], '#food', uv=[0, 0, 4, 2], side_uv=[0, 0, 4, 2]))
                elements.append(uniform_box([9, 1, 9], [11, 2, 11], '#food', uv=[10, 0, 13, 2], side_uv=[10, 0, 13, 2]))
            else:
                # Fresh Cabbage & Herb Garnish Bed + Roasted Carrot Sticks
                elements.append(uniform_box([3, 1, 3], [13, 1.6, 13], '#herb', uv=[2, 2, 14, 14], side_uv=[2, 14, 14, 16]))
                elements.append(uniform_box([3.2, 1.5, 11.2], [5.8, 2.4, 12.8], '#carrot', uv=[2, 2, 6, 4], side_uv=[2, 2, 6, 4]))
                elements.append(uniform_box([10.2, 1.5, 3.2], [12.8, 2.4, 4.8], '#carrot', uv=[2, 2, 6, 4], side_uv=[2, 2, 6, 4]))
            feast_portions = [
                # Portion 1 (NW): Roasted Infernal Dragon Steak + Protruding 3D Dragon Bone Knob
                [
                    uniform_box([3.4, 1.5, 3.4], [8.0, 4.5, 8.0], '#food', uv=[0, 0, 8, 8], side_uv=[0, 2, 8, 7]),
                    uniform_box([3.0, 3.6, 3.0], [5.4, 5.5, 5.4], '#food', uv=[0, 0, 4, 3], side_uv=[0, 0, 4, 3]),
                ],
                # Portion 2 (NE): Cooked Frost Yeti Roast + Protruding 3D Icy-Cyan Permafrost Horn
                [
                    uniform_box([8.0, 1.5, 3.4], [12.6, 4.5, 8.0], '#food', uv=[8, 0, 16, 8], side_uv=[8, 2, 16, 7]),
                    uniform_box([10.2, 3.6, 3.0], [12.6, 5.5, 5.4], '#food', uv=[9, 0, 15, 3], side_uv=[9, 0, 15, 3]),
                ],
                # Portion 3 (SW): Purified Sandworm Chitin Fillet + Dorsal Chitin Ridge
                [
                    uniform_box([3.4, 1.5, 8.0], [8.0, 4.2, 12.6], '#food', uv=[0, 8, 8, 16], side_uv=[0, 9, 8, 15]),
                    uniform_box([4.2, 4.2, 8.8], [7.2, 5.1, 11.8], '#food', uv=[1, 8, 7, 13], side_uv=[1, 8, 7, 12]),
                ],
                # Portion 4 (SE): Grilled Kraken Tentacle Coil + Curled Tentacle Tip Arch
                [
                    uniform_box([8.0, 1.5, 8.0], [12.6, 4.2, 12.6], '#food', uv=[8, 8, 15, 15], side_uv=[8, 9, 15, 15]),
                    uniform_box([9.2, 4.2, 9.2], [12.0, 5.3, 12.0], '#food', uv=[9, 9, 14, 14], side_uv=[9, 9, 14, 13]),
                ],
            ]
            for grp in feast_portions[:servings]:
                elements.extend(grp)
        model = {'parent': 'minecraft:block/block', 'render_type': 'minecraft:cutout',
                 'display': FEAST_DISPLAY,
                 'textures': {'particle': f'{MOD}:block/' + ('tentacle' if hotpot else 'roast'),
                              'tray': 'farmersdelight:block/tray', 'tray_bottom': 'farmersdelight:block/tray_bottom',
                              'metal': f'{MOD}:block/metal',
                              'broth': f'{MOD}:block/broth', 'food': f'{MOD}:block/' + ('tentacle' if hotpot else 'roast'),
                              'carrot': 'minecraft:block/orange_terracotta', 'herb': 'minecraft:block/moss_block'},
                 'elements': elements}
        write(RES / f'assets/{MOD}/models/block/{name}_{servings}.json', model)
        for facing, rotation in [('north', 0), ('east', 90), ('south', 180), ('west', 270)]:
            variants[f'facing={facing},servings={servings}'] = {'model': f'{MOD}:block/{name}_{servings}', 'y': rotation}
    write(RES / f'assets/{MOD}/blockstates/{name}.json', {'variants': variants})
    full = {'condition': 'minecraft:block_state_property', 'block': item(name), 'properties': {'servings': '4'}}
    write(RES / f'data/{MOD}/loot_table/blocks/{name}.json', {'type': 'minecraft:block', 'pools': [
        {'rolls': 1, 'conditions': [full, {'condition': 'minecraft:survives_explosion'}],
         'entries': [{'type': 'minecraft:item', 'name': item(name)}]},
        {'rolls': 1, 'conditions': [{'condition': 'minecraft:inverted', 'term': full}, {'condition': 'minecraft:survives_explosion'}],
         'entries': [{'type': 'minecraft:item', 'name': 'minecraft:bowl'}]}
    ]})

def generate():
    english, chinese = {}, {}
    declarations = []
    for name, en, zh, nutrition, saturation, bowl, effects, note in FOODS:
        english[f'item.{MOD}.{name}'], chinese[f'item.{MOD}.{name}'] = en, zh
        builder = f'new FoodProperties.Builder().nutrition({nutrition}).saturationModifier({saturation}F)'
        custom = [(effect, seconds, amplifier) for effect, seconds, amplifier in effects if effect in EFFECTS]
        for effect, seconds, probability in effects:
            if effect in EFFECTS: continue
            builder += f'.effect(() -> new MobEffectInstance(MobEffects.{effect.upper()}, {seconds * 20}), {float(probability)}F)'
        if custom: builder += '.alwaysEdible()'
        properties = 'new Item.Properties().food(' + builder + '.build())'
        if bowl: properties += '.craftRemainder(Items.BOWL).stacksTo(16)'
        note_string = json.dumps(note) if note else 'null'
        bonuses = 'List.of(' + ', '.join(f'new MealBonus(CulinaryEffects.{effect.upper()}, {seconds}, {amplifier})' for effect, seconds, amplifier in custom) + ')'
        declarations.append(f'    public static final DeferredItem<HuntingMealItem> {name.upper()} = register("{name}", () -> new HuntingMealItem({properties}, {note_string}, {bonuses}));')
        write(RES / f'assets/{MOD}/models/item/{name}.json', {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{MOD}:item/{name}'}})
    for name, en, zh, note in SEASONINGS:
        english[f'item.{MOD}.{name}'], chinese[f'item.{MOD}.{name}'] = en, zh
        declarations.append(f'    public static final DeferredItem<SeasoningItem> {name.upper()} = register("{name}", () -> new SeasoningItem(new Item.Properties().fireResistant(), "{note}"));')
        write(RES / f'assets/{MOD}/models/item/{name}.json', {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{MOD}:item/{name}'}})
    for name, en, zh in [('dragonbone_knife', 'Dragonbone Chef Knife', '龙骨厨刀'), ('krakentooth_knife', 'Krakentooth Chef Knife', '克拉肯牙厨刀')]:
        english[f'item.{MOD}.{name}'], chinese[f'item.{MOD}.{name}'] = en, zh
        write(RES / f'assets/{MOD}/models/item/{name}.json', {'parent': f'{MOD}:item/knife_handheld', 'textures': {'layer0': f'{MOD}:item/{name}'}})
    for name, en, zh in [('hunters_feast', "Hunter's Feast", '猎人盛宴'), ('kraken_hotpot', 'Kraken Hotpot', '克拉肯海鲜火锅')]:
        english[f'block.{MOD}.{name}'], chinese[f'block.{MOD}.{name}'] = en, zh
        english[f'tooltip.{MOD}.{name}'], chinese[f'tooltip.{MOD}.{name}'] = 'Place on a solid surface. Use a bowl to take one of four servings.', '放在坚固表面上，用碗取食；共四份。'
        write(RES / f'assets/{MOD}/models/item/{name}.json', {'parent': f'{MOD}:block/{name}_4'})
        feast_models(name, name == 'kraken_hotpot')
    for name, en, zh in [
        ('dragon_source', 'A hunting ingredient from Ashlord, the Infernal Dragon.', '击败炼狱龙阿什洛德获得的狩猎食材。'),
        ('yeti_source', 'A hunting ingredient from Skor, the Yeti.', '击败霜冻雪怪斯科尔获得的狩猎食材。'),
        ('worm_source', 'Poisonous raw. Clean with a knife on a cutting board.', '生食有毒。可用刀在切菜板上净化。'),
        ('kraken_source', 'A hunting ingredient from Nerakyss, the Kraken.', '击败深海巨妖克拉肯获得的狩猎食材。'),
        ('cleaned_worm', 'The toxic membrane has been removed. Ready for cooking.', '已去除有毒外膜，可用于烹饪。')]:
        english[f'tooltip.{MOD}.{name}'], chinese[f'tooltip.{MOD}.{name}'] = en, zh
    english[f'itemGroup.{MOD}'], chinese[f'itemGroup.{MOD}'] = "Bosses'Rise Delight", '首领乐事'
    for effect, (en, zh, desc_en, desc_zh) in EFFECTS.items():
        english[f'effect.{MOD}.{effect}'], chinese[f'effect.{MOD}.{effect}'] = en, zh
        english[f'effect.{MOD}.{effect}.description'], chinese[f'effect.{MOD}.{effect}.description'] = desc_en, desc_zh
    for key, en, zh in [
        ('tooltip.battle_meal', 'Battle meal - edible even at full hunger', '战斗料理 · 满饥饿时也可食用'),
        ('tooltip.bonus', '%s (%s)', '%s（%s）'),
        ('tooltip.nether_ember', 'Dropped by Helvar. Crush on a cutting board to make Soul Salt.', '击败冥界骑士获得；在切菜板上研磨为灵魂盐。'),
        ('tooltip.soul_salt', 'Soul seasoning for the Nether Knight cuisine.', '冥界骑士料理的灵魂调味料。'),
        ('message.war_souls', 'War souls: %s / 3', '战魂：%s / 3'),
        ('message.soul_saved', 'Three war souls protected you. Soul Harvest has ended.', '三层战魂护住了你，战魂盛宴效果已结束。'),
        ('tooltip.knife.dragonbone', 'Diamond-tier knife; dropped item is fire-resistant.', '钻石级厨刀 · 掉落物耐火'),
        ('tooltip.knife.krakentooth', 'Iron-tier chef knife.', '铁级厨刀'),
        ('tooltip.knife.hunting', 'Hunting bonus: +%s boss ingredients', '狩猎加成：首领食材额外 +%s'),
        ('tooltip.knife.hunting_default', 'Hunting bonus: +%s boss ingredients (default)', '狩猎加成：首领食材额外 +%s（默认）'),
        ('tooltip.knife.hunting_disabled', 'The hunting bonus is disabled in this world.', '当前世界关闭了狩猎加成'),
        ('tooltip.knife.condition', 'Hold a knife in your main hand when credited boss loot is generated.', '首领掉落生成时，击杀者主手持厨刀生效。'),
        ('tooltip.knife.shared', 'Shared knife reward; cutting yields are unchanged.', '厨刀通用奖励 · 不增加切菜产量'),
        ('tooltip.knife.utility', 'Cutting board, cake slices and pumpkin carving.', '可用于切菜、蛋糕切片和南瓜雕刻。'),
    ]:
        kind, short = key.split('.', 1)
        english[f'{kind}.{MOD}.{short}'], chinese[f'{kind}.{MOD}.{short}'] = en, zh
    english[f'death.attack.{MOD}.culinary'] = '%1$s was overcome by culinary power'
    chinese[f'death.attack.{MOD}.culinary'] = '%1$s被料理之力击倒了'
    english[f'death.attack.{MOD}.culinary.player'] = "%1$s was overcome by %2$s's culinary power"
    chinese[f'death.attack.{MOD}.culinary.player'] = '%1$s被%2$s的料理之力击倒了'
    for lang, values in [('en_us', english), ('zh_cn', chinese)]: write(RES / f'assets/{MOD}/lang/{lang}.json', values)

    java = '''package com.suiyi.bossesrisedelight;

import com.suiyi.bossesrisedelight.item.HuntingMealItem;
import com.suiyi.bossesrisedelight.item.HuntingFeastItem;
import com.suiyi.bossesrisedelight.item.SeasoningItem;
import com.suiyi.bossesrisedelight.item.ChefKnifeItem;
import com.suiyi.bossesrisedelight.effect.CulinaryEffects;
import com.suiyi.bossesrisedelight.effect.MealBonus;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.*;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import vectorwing.farmersdelight.common.item.KnifeItem;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

/** Generated by tools/generate_resources.py; tune the food catalogue there. */
public final class DelightItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(BossesRiseDelight.MOD_ID);
    public static final List<DeferredItem<? extends Item>> ALL = new ArrayList<>();
    private static <T extends Item> DeferredItem<T> register(String name, Supplier<T> supplier) {
        DeferredItem<T> item = ITEMS.register(name, supplier);
        ALL.add(item);
        return item;
    }
'''
    java += '\n'.join(declarations)
    java += '''
    public static final DeferredItem<KnifeItem> DRAGONBONE_KNIFE = register("dragonbone_knife",
            () -> new ChefKnifeItem(Tiers.DIAMOND, new Item.Properties().fireResistant()
                    .attributes(KnifeItem.createAttributes(Tiers.DIAMOND, 0.5F, -2.0F)), "dragonbone"));
    public static final DeferredItem<KnifeItem> KRAKENTOOTH_KNIFE = register("krakentooth_knife",
            () -> new ChefKnifeItem(Tiers.IRON, new Item.Properties()
                    .attributes(KnifeItem.createAttributes(Tiers.IRON, 0.5F, -2.0F)), "krakentooth"));
    public static final DeferredItem<BlockItem> HUNTERS_FEAST = register("hunters_feast",
            () -> new HuntingFeastItem(DelightBlocks.HUNTERS_FEAST.get(), new Item.Properties()));
    public static final DeferredItem<BlockItem> KRAKEN_HOTPOT = register("kraken_hotpot",
            () -> new HuntingFeastItem(DelightBlocks.KRAKEN_HOTPOT.get(), new Item.Properties()));
    private DelightItems() {}
}
'''
    path = ROOT / 'src/main/java/com/suiyi/bossesrisedelight/DelightItems.java'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(java, encoding='utf-8')

    for raw, cooked in [('raw_dragon_cut', 'roasted_dragon_cut'), ('raw_yeti_cut', 'cooked_yeti_cut'), ('raw_kraken_tentacle', 'grilled_kraken_tentacle')]:
        for kind, time in [('smelting', 200), ('smoking', 100), ('campfire_cooking', 600)]:
            recipe(f'{kind}/{cooked}', {'type': f'minecraft:{kind}', 'category': 'food', 'ingredient': ingredient(raw),
                                      'result': {'id': item(cooked)}, 'experience': .35, 'cookingtime': time})
    cutting('clean_sandworm', 'raw_sandworm_fillet', 'purified_sandworm_fillet', 2)
    cutting('dragon_shank', 'block_factorys_bosses:dragon_shank', 'raw_dragon_cut', 2)
    # Feast portions require an actual bowl interaction; cutting would create free bowls.
    shapeless('dragon_skewer', ['roasted_dragon_cut', 'minecraft:stick'])
    cooking('dragon_curry', ['raw_dragon_cut', '#c:crops/potato', 'farmersdelight:tomato', 'minecraft:carrot'])
    shapeless('dragon_sandwich', ['roasted_dragon_cut', 'minecraft:bread', 'farmersdelight:cabbage_leaf', 'farmersdelight:tomato'])
    cooking('yeti_stew', ['raw_yeti_cut', 'minecraft:potato', 'minecraft:carrot', 'minecraft:brown_mushroom'])
    cooking('yeti_dumplings', ['raw_yeti_cut', 'farmersdelight:wheat_dough', 'farmersdelight:cabbage_leaf'])
    shapeless('frosted_berry_tart', ['minecraft:sweet_berries', 'minecraft:sugar', 'minecraft:snowball', 'farmersdelight:pie_crust'])
    shapeless('sandworm_wrap', ['purified_sandworm_fillet', 'minecraft:bread', 'farmersdelight:cabbage_leaf', 'farmersdelight:tomato'])
    cooking('desert_stew', ['purified_sandworm_fillet', 'minecraft:carrot', 'minecraft:potato', 'minecraft:brown_mushroom'])
    cooking('sandworm_rice', ['purified_sandworm_fillet', 'farmersdelight:rice', 'minecraft:carrot'])
    cooking('kraken_calamari', ['raw_kraken_tentacle', 'farmersdelight:wheat_dough', 'minecraft:egg'])
    cooking('kraken_chowder', ['raw_kraken_tentacle', 'minecraft:potato', 'minecraft:brown_mushroom', 'minecraft:kelp'])
    cooking('sea_noodles', ['raw_kraken_tentacle', 'farmersdelight:raw_pasta', 'minecraft:dried_kelp', 'minecraft:carrot'])
    shapeless('hunters_feast', ['roasted_dragon_cut', 'cooked_yeti_cut', 'purified_sandworm_fillet', 'grilled_kraken_tentacle', 'minecraft:carrot', 'farmersdelight:tomato', 'farmersdelight:cabbage_leaf', 'minecraft:bowl'])
    shapeless('kraken_hotpot', ['grilled_kraken_tentacle', 'grilled_kraken_tentacle', 'minecraft:cooked_cod', 'minecraft:cooked_salmon', 'minecraft:dried_kelp', 'minecraft:carrot', 'minecraft:bowl', 'minecraft:iron_ingot'])
    recipe('crafting/dragonbone_knife', {'type': 'minecraft:crafting_shaped', 'category': 'equipment', 'pattern': [' D', 'S '],
                                     'key': {'D': ingredient('block_factorys_bosses:dragon_bone'), 'S': ingredient('minecraft:stick')}, 'result': {'id': item('dragonbone_knife')}})
    recipe('crafting/krakentooth_knife', {'type': 'minecraft:crafting_shaped', 'category': 'equipment', 'pattern': [' T', 'S '],
                                      'key': {'T': ingredient('block_factorys_bosses:kraken_tooth'), 'S': ingredient('minecraft:stick')}, 'result': {'id': item('krakentooth_knife')}})
    cutting('soul_salt', 'nether_ember', 'soul_salt', 2)
    cooking('soul_braised_meat', ['soul_salt', '#c:foods/raw_beef', 'minecraft:potato', 'minecraft:brown_mushroom'])
    cooking('soulfire_noodles', ['soul_salt', 'farmersdelight:raw_pasta', '#c:foods/raw_beef', 'farmersdelight:tomato'])
    shapeless('nightwatch_pie', ['soul_salt', 'minecraft:cooked_beef', 'farmersdelight:pie_crust', 'minecraft:brown_mushroom'])

    modifiers = []
    boss_ingredients = [('infernal_dragon', 'raw_dragon_cut'), ('yeti', 'raw_yeti_cut'), ('sandworm', 'raw_sandworm_fillet'), ('kraken', 'raw_kraken_tentacle'), ('underworld_knight', 'nether_ember')]
    for boss, food in boss_ingredients:
        modifiers.append(item(boss + '_ingredient'))
        write(RES / f'data/{MOD}/loot_modifiers/{boss}_ingredient.json', {
            'type': item('boss_ingredient'), 'conditions': [
                {'condition': 'neoforge:loot_table_id', 'loot_table_id': f'block_factorys_bosses:entities/{boss}'},
                {'condition': 'minecraft:killed_by_player'}], 'ingredient': item(food), 'minimum': 6, 'maximum': 10})
    write(RES / 'data/neoforge/loot_modifiers/global_loot_modifiers.json', {'replace': False, 'entries': modifiers})
    tags = {
        'c:tools/knife': ['dragonbone_knife', 'krakentooth_knife'],
        'c:foods': [f[0] for f in FOODS],
        'c:foods/raw_meat': [f[0] for f in FOODS[:4]],
        'c:foods/cooked_meat': ['roasted_dragon_cut', 'cooked_yeti_cut', 'grilled_kraken_tentacle'],
        'c:foods/soup': ['dragon_curry', 'yeti_stew', 'desert_stew', 'kraken_chowder', 'kraken_hotpot_serving', 'soul_braised_meat'],
        'farmersdelight:feasts': ['hunters_feast', 'kraken_hotpot'],
        'c:edible_when_placed': ['hunters_feast', 'kraken_hotpot'],
        'block_factorys_bosses:glowing_loot': [food for boss, food in boss_ingredients],
    }
    for tag, names in tags.items():
        ns, path = tag.split(':')
        write(RES / f'data/{ns}/tags/item/{path}.json', {'replace': False, 'values': list(map(item, names))})
    write(RES / f'data/{MOD}/tags/block/feasts.json', {'replace': False, 'values': [item('hunters_feast'), item('kraken_hotpot')]})
    advancement('first_ingredient', 'raw_dragon_cut', 'A Taste of Victory', '胜利的滋味', 'Obtain an ingredient from a defeated boss.', '获得一份首领食材。', [food for boss, food in boss_ingredients], True)
    advancement('all_ingredients', 'hunters_feast', 'Five Hunts, One Kitchen', '五方狩猎，一间厨房', 'Collect all five boss ingredients.', '收集全部五种首领食材。', [food for boss, food in boss_ingredients], False, 'first_ingredient')
    advancement('share_the_feast', 'hunters_feast', 'Dinner Is Served', '盛宴开席', 'Prepare a shareable feast.', '制作一份可以分享的宴席。', ['hunters_feast', 'kraken_hotpot'], True, 'all_ingredients')
    advancement('soul_cuisine', 'soul_braised_meat', 'A Knight at the Table', '骑士赴宴', 'Prepare a soul-seasoned meal.', '制作一道冥界骑士料理。', [food[0] for food in NETHER_FOODS], True, 'first_ingredient')
    write(RES / f'data/{MOD}/damage_type/culinary.json', {'message_id': f'{MOD}.culinary', 'scaling': 'never', 'exhaustion': .1, 'effects': 'hurt'})
    for tag_name in ['bypasses_cooldown', 'no_knockback']:
        write(RES / f'data/minecraft/tags/damage_type/{tag_name}.json', {'replace': False, 'values': [item('culinary')]})
    for path in (RES / f'data/{MOD}/recipe').rglob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        if not data['type'].startswith('minecraft:'): continue
        candidates = data.get('ingredients') or list(data.get('key', {}).values()) or [data.get('ingredient')]
        source = next(value['item'] for value in candidates if value and 'item' in value)
        recipe_id = item(path.relative_to(RES / f'data/{MOD}/recipe').with_suffix('').as_posix())
        write(RES / f'data/{MOD}/advancement/recipes' / path.relative_to(RES / f'data/{MOD}/recipe'), {
            'parent': 'minecraft:recipes/root',
            'criteria': {'has_ingredient': {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': [source]}]}},
                         'has_recipe': {'trigger': 'minecraft:recipe_unlocked', 'conditions': {'recipe': recipe_id}}},
            'requirements': [['has_ingredient', 'has_recipe']], 'rewards': {'recipes': [recipe_id]}})
    # Tiny empty template used by development-only integration tests, excluded from release jars.
    def string(text):
        data = text.encode(); return struct.pack('>H', len(data)) + data
    def tag(kind, name, payload): return bytes([kind]) + string(name) + payload
    root = tag(3, 'DataVersion', struct.pack('>i', 3955))
    root += tag(9, 'size', bytes([3]) + struct.pack('>i', 3) + struct.pack('>iii', 5, 5, 5))
    root += tag(9, 'palette', bytes([10]) + struct.pack('>i', 1) + tag(8, 'Name', string('minecraft:air')) + b'\0')
    root += tag(9, 'blocks', bytes([10]) + struct.pack('>i', 0))
    root += tag(9, 'entities', bytes([10]) + struct.pack('>i', 0))
    nbt = bytes([10]) + string('') + root + b'\0'
    dest = RES / f'data/{MOD}/structure/empty.nbt'; dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(gzip.compress(nbt, mtime=0))
    write(ROOT / 'docs/food-catalogue.json', [dict(zip(['id', 'en', 'zh', 'nutrition', 'saturation', 'bowl', 'effects', 'note'], row)) for row in FOODS])
    write(ROOT / 'docs/effect-catalogue.json', [{'id': effect, 'en': values[0], 'zh': values[1], 'description': values[3], 'beneficial': effect not in ['rimebound', 'corrosive_venom']} for effect, values in EFFECTS.items()])
    write(ROOT / 'docs/seasoning-catalogue.json', [{'id': name, 'en': en, 'zh': zh} for name, en, zh, note in SEASONINGS])
    write(ROOT / 'docs/content-summary.json', {'foods': len(FOODS), 'seasonings': len(SEASONINGS), 'knives': 2, 'feasts': 2, 'items': len(FOODS) + len(SEASONINGS) + 4, 'effects': len(EFFECTS), 'textures': 4 + len(FOODS) + len(SEASONINGS) + 2 + len(EFFECTS), 'recipes': len(list((RES / f'data/{MOD}/recipe').rglob('*.json')))})
    print(f'Generated {len(FOODS)} foods, 2 seasonings, 2 knives, 2 feasts, {len(EFFECTS)} original effects; 31 recipes.')

def advancement(name, icon, en, zh, desc_en, desc_zh, foods, either, parent=None):
    display = {'icon': {'id': item(icon)}, 'title': {'translate': f'advancement.{MOD}.{name}'},
               'description': {'translate': f'advancement.{MOD}.{name}.desc'}, 'frame': 'task', 'show_toast': True, 'announce_to_chat': True}
    if not parent: display['background'] = 'minecraft:textures/block/stripped_oak_log.png'
    values = {'display': display, 'criteria': {f: {'trigger': 'minecraft:inventory_changed', 'conditions': {'items': [{'items': [item(f)]}]}} for f in foods},
              'requirements': [foods] if either else [[f] for f in foods]}
    if parent: values['parent'] = item(parent)
    write(RES / f'data/{MOD}/advancement/{name}.json', values)
    for lang, title, description in [('en_us', en, desc_en), ('zh_cn', zh, desc_zh)]:
        path = RES / f'assets/{MOD}/lang/{lang}.json'; translations = json.loads(path.read_text(encoding='utf-8'))
        translations[f'advancement.{MOD}.{name}'] = title
        translations[f'advancement.{MOD}.{name}.desc'] = description
        write(path, translations)

if __name__ == '__main__': generate()
