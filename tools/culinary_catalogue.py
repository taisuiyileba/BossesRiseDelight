"""Original combat meal profiles and their user-facing explanations."""
# effect id: English name, Chinese name, English description, Chinese description
EFFECTS = {
    'ember_appetite': ('Ember Appetite', '龙焰余烬', 'Three melee hits trigger a 4-damage burst and 2 damage to nearby hostiles. 2s cooldown; stronger at higher tiers.', '连续三次近战触发4点火爆，波及附近敌人2点；冷却2秒，等级提高伤害。'),
    'blaze_digest': ('Blaze Digest', '烈焰回甘', 'Reduce fire damage by 60%; a fire hit can restore 1.5 health every 4s.', '火焰伤害减少60%；受火伤后可回复1.5点生命，冷却4秒。'),
    'frost_shell': ('Frost Shell', '霜壳', 'A 4-point frost shield shatters into chilling mist. Rebuild after 6s without damage.', '生成4点霜盾，破碎时释放寒气；6秒未受伤后重建。等级提高护盾量。'),
    'frost_reprisal': ('Frost Reprisal', '冰牙反击', 'Taking damage counters a nearby attacker for 3 frost damage and slows them. 4s cooldown.', '受击时对附近攻击者反击3点寒霜伤害并减速；冷却4秒。等级提高伤害。'),
    'sand_surge': ('Sand Surge', '涌沙', 'Starting a sprint or boss roll arms your next melee hit for +3 damage for 2s. 4s cooldown.', '冲刺或翻滚起手后2秒内，下一次近战追加3点伤害；冷却4秒。冲刺额外小幅突进。'),
    'venom_sac': ('Venom Sac', '毒囊', 'Melee hits apply corrosive venom for 4s: armor erosion and damage each second. 3s cooldown.', '近战附加4秒腐毒，侵蚀护甲并每秒造成伤害；施毒冷却3秒。'),
    'tidal_echo': ('Tidal Echo', '潮汐回响', 'Melee hits echo after 0.6s for 2-5 extra damage. 3s cooldown; higher tiers strengthen the echo.', '近战命中0.6秒后追击一次，追加2~5点伤害；冷却3秒。等级强化追击。'),
    'abyss_gills': ('Abyss Gills', '深渊腮息', 'Restore air underwater; spend 80 air to absorb up to 35% of a hit (max 4). 5s guard cooldown.', '水下补充空气；消耗80点空气抵挡最多35%的伤害，上限4点，冷却5秒。等级提高补气与上限。'),
    'soul_harvest': ('Soul Harvest', '战魂盛宴', 'Hostile kills collect up to 3 war souls. Spend all 3 to survive one lethal hit at 1 health; this effect ends.', '击杀敌对生物收集战魂，最多3层；消耗三层抵挡一次致命伤并保留1点生命，随后效果结束。'),
    'nether_resolve': ('Nether Resolve', '冥骑决意', 'Taking damage below 40% health opens a 3s counter window: next melee +4 damage and heal 2. 8s cooldown.', '生命低于40%时受击，开启3秒反击窗口；下一次近战追加4点伤害并回复2点生命，冷却8秒。'),
    'hunter_resonance': ('Hunter Resonance', '狩猎共鸣', 'Hostile kills restore 2 health to you and allies within 6 blocks. 1s cooldown.', '击杀敌对生物时，为自己及6格内友军回复2点生命；冷却1秒。'),
    'rimebound': ('Rimebound', '霜缚', 'Chilling mist reduces movement speed by 18%.', '受到寒气束缚，移动速度降低18%。'),
    'corrosive_venom': ('Corrosive Venom', '腐毒侵蚀', 'Armor is reduced by 12%; culinary poison deals damage every second.', '护甲降低12%，每秒受到腐毒伤害。'),
}

# Custom effect entries are (id, seconds, amplifier); amplifier 0 means level I.
MEAL_PROFILES = {
    'roasted_dragon_cut': [('ember_appetite', 60, 0)],
    'cooked_yeti_cut': [('frost_shell', 60, 0)],
    'purified_sandworm_fillet': [('venom_sac', 60, 0)],
    'grilled_kraken_tentacle': [('tidal_echo', 60, 0)],
    'dragon_skewer': [('ember_appetite', 120, 1)],
    'dragon_curry': [('ember_appetite', 180, 1), ('blaze_digest', 120, 0)],
    'dragon_sandwich': [('blaze_digest', 180, 0)],
    'yeti_stew': [('frost_shell', 180, 1), ('frost_reprisal', 90, 0)],
    'yeti_dumplings': [('frost_reprisal', 180, 1)],
    'frosted_berry_tart': [('frost_shell', 90, 0)],
    'sandworm_wrap': [('sand_surge', 180, 0)],
    'desert_stew': [('venom_sac', 180, 1)],
    'sandworm_rice': [('sand_surge', 180, 0), ('venom_sac', 120, 0)],
    'kraken_calamari': [('tidal_echo', 180, 1)],
    'kraken_chowder': [('abyss_gills', 240, 0)],
    'sea_noodles': [('tidal_echo', 180, 0), ('abyss_gills', 120, 0)],
    'hunters_feast_serving': [('hunter_resonance', 240, 0), ('ember_appetite', 120, 1), ('frost_shell', 120, 1)],
    'kraken_hotpot_serving': [('tidal_echo', 240, 1), ('abyss_gills', 240, 1)],
}

NETHER_FOODS = [
    ('soul_braised_meat', 'Soul-Braised Meat', '冥骑炖肉', 12, .9, True, [('soul_harvest', 240, 0)], None),
    ('soulfire_noodles', 'Soulfire Noodles', '灵火面', 10, .8, True, [('soul_harvest', 180, 0), ('nether_resolve', 120, 0)], None),
    ('nightwatch_pie', 'Nightwatch Pie', '守夜馅饼', 10, .8, False, [('nether_resolve', 240, 0)], None),
]
SEASONINGS = [('nether_ember', 'Nether Ember', '冥火余烬', 'nether_ember'), ('soul_salt', 'Soul Salt', '灵魂盐', 'soul_salt')]
