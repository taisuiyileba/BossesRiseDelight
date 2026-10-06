# Bosses'Rise Delight / 首领乐事

Minecraft **1.21.1** · NeoForge **21.1.219+** · Java **21** · 版本 **1.0.0**。

首领崛起 × 农夫乐事附属：五条首领食材路线、料理、厨刀、共享宴席，以及能改变战斗方式的原创餐食效果。

## 安装

将编译生成的 `bossesrise-delight-1.21.1-neoforge-1.0.0.jar`（或发布包）放入游戏 `mods` 目录；客户端和服务端均需安装。前置：

- [Bosses'Rise 2.1.2](https://modrinth.com/mod/bossesrise/version/lE9PF6Wp)
- [Farmer's Delight 1.3.4](https://modrinth.com/mod/farmers-delight/version/XTVZDOol)
- [GeckoLib 4.8.2](https://modrinth.com/mod/geckolib/version/RVIo5f6E)，首领崛起的前置

发布 jar 只含本附属代码和资源，前置单独安装。当前只实现 1.21.1 NeoForge。

## 内容

**25 个可食用物品、2 种冥骑调味材料、2 把厨刀、2 个宴席方块、31 条配方。共 11 种原创增益，另有霜缚和腐毒侵蚀两种负面效果。**

| 路线 | 食材和料理 | 战斗特色 |
| --- | --- | --- |
| 炼狱龙 | 龙肉、烤串、咖喱、三明治 | 三连火爆、火伤转化回血 |
| 雪怪 | 雪怪肉、炖汤、肉饺、莓果挞 | 霜盾重建、冰牙反击 |
| 沙虫 | 净化肉、卷饼、炖汤、盖饭 | 冲刺／翻滚后突击、腐毒侵蚀 |
| 克拉肯 | 触手、炸圈、浓汤、面条 | 延迟追击、补气和耗气防御 |
| 冥界骑士 | 冥火余烬、灵魂盐、冥骑炖肉、灵火面、守夜馅饼 | 收集战魂护命、低血量反击 |
| 共享宴席 | 猎人盛宴、克拉肯海鲜火锅 | 四份分餐、组合增益和团队恢复 |

原有熟食和料理全部使用原创效果。生肉保留饥饿／中毒等生食惩罚。21 种带有专属效果的熟食和料理支持满饥饿食用，方便战前补充效果。物品提示显示名称、等级、持续时间和触发方式。详细搭配见 [`docs/custom-effects.md`](docs/custom-effects.md)。

## 获取与加工

1. 玩家击败五个首领时，追加 6～10 份食材或冥火余烬，保留原战利品。归属玩家当前主手持厨刀时默认增加 2 份。
2. 龙肉、雪怪肉、触手可用熔炉、烟熏炉、营火处理。沙虫生肉先在切菜板上净化，每段获得两份净化肉。
3. 冥火余烬在切菜板上研磨，一份获得两份灵魂盐。
4. 灵魂盐配生牛肉、土豆和蘑菇，在烹饪锅里制成冥骑炖肉；配面条、生牛肉和番茄制成灵火面；配熟牛肉、派皮和蘑菇合成守夜馅饼。
5. 碗装料理吃完返还一个碗，堆叠食用也正确返还。
6. 宴席放在坚固表面，用碗右键领取，共四份，每次消耗一个实际持有的碗。空盘打破或再次右键返还宴席本身的一个碗；使用过的宴席不会恢复为全新宴席。

**宴席不设切菜板分餐配方。** 合成使用一个碗，领取四份料理另外使用四个碗，食用和清理后总计返还五个碗，不会凭空生成容器。原版合成／烧炼配方有配方书解锁进度；锅和切菜板使用农夫乐事的加工机制，四项主题进度提供基本引导。

## 厨刀

- 龙骨厨刀使用钻石级材质，耐久较高，掉落成物品后耐火。
- 克拉肯牙厨刀使用铁级材质。
- 两者继承农夫乐事的切菜板加工、蛋糕切片、南瓜雕刻等厨刀功能。
- 首领掉落归属玩家当前主手持有效厨刀时，默认额外增加两份食材；这个奖励适用于所有有效厨刀，不是两把附属刀的独占技能，可通过`knifeBonus`配置。
- 当前两把刀没有独立主动技能或额外战斗触发能力。

两把厨刀拥有完备的中英文物品提示。狩猎奖励数值随当前世界设置显示，未加载世界时显示默认值；关闭额外掉落或持刀奖励时提示其已关闭。说明明确区分首领追加掉落和切菜产量，并保留厨刀材质与龙骨刀掉落物耐火的提示。两把厨刀的手持刀刃朝向均已正确覆盖第一／第三人称和左右手。

## 原创效果

| 效果 | 等级 I 默认行为 |
| --- | --- |
| 龙焰余烬 | 同一目标八秒内三次近战命中，触发4点火爆，波及附近敌人2点；冷却2秒 |
| 烈焰回甘 | 火焰伤害减少60%，受火伤后回复1.5点生命；回血冷却4秒 |
| 霜壳 | 4点霜盾，破碎时释放寒气；破碎后6秒未受伤则重建。等级II为6点盾 |
| 冰牙反击 | 受击时反击8格内攻击者，造成3点伤害并施加霜缚；冷却4秒 |
| 涌沙 | 冲刺／翻滚起手后两秒内，下一次近战追加3点伤害；冷却4秒。冲刺额外小幅突进 |
| 毒囊 | 近战施加4秒腐毒侵蚀，每秒伤害并侵蚀护甲；施毒冷却3秒 |
| 潮汐回响 | 命中0.6秒后追击，伤害为原命中的30%，限制在2～5点；冷却3秒 |
| 深渊腮息 | 水下每秒补30点空气；消耗80点空气抵挡最多35%的伤害，上限4点，冷却5秒 |
| 战魂盛宴 | 敌对生物击杀积累战魂，最多三层；消耗三层保住一次致命伤后的1点生命，随后效果结束 |
| 冥骑决意 | 生命低于40%时受击开启三秒反击窗口；下一次近战追加4点伤害并回复2点生命，冷却8秒 |
| 狩猎共鸣 | 击杀敌对生物，为自己和六格内友军回复2点生命；冷却1秒 |

等级、时间、组合随料理变化。霜缚降低移动速度；腐毒侵蚀降低护甲并持续伤害。料理额外伤害仍经过护甲及原模组受伤判定，不会再次触发火爆、腐毒或追击。战魂不从被动动物或玩家击杀中获得；护命考虑吸收心，也不阻止虚空等绕过无敌判定的伤害。

## 配置

世界的 `serverconfig/bossesrise_delight-server.toml`：

```toml
[hunting]
ingredientDrops = true
dropMultiplier = 1
knifeBonus = 2

[cuisine]
customMealEffects = true
effectDurationScale = 1.0
procDamageScale = 1.0
pvpProcs = false
```

可调整食材产量、持刀奖励、专属效果开关、时长、额外伤害倍率、是否允许对玩家触发进攻型料理效果。普通武器伤害不受料理倍率影响。数据包可覆盖配方、掉落条件和标签。

## 贴图与验证

食材与料理图标为原创 16×16，效果图标采用 Minecraft 原生 18×18；有限配色、二值透明度、按轮廓居中。

- [`docs/texture-preview.png`](docs/texture-preview.png)：全部物品贴图。
- [`docs/effect-preview.png`](docs/effect-preview.png)：原创效果图标。
- [`docs/in-game-preview.png`](docs/in-game-preview.png)：实际客户端渲染。
- [`docs/verification-report.json`](docs/verification-report.json)：验证记录。

20 项游戏内测试覆盖五个首领掉落表、加工配方、满饥饿食用、两种宴席容器守恒、额外伤害与冷却、霜盾重建、真实水中补气与防御、战魂护命、吸收心、虚空伤害和默认玩家攻击规则。客户端检查全部 31 个物品模型和 13 个效果图标。当前为 1.0.0 正式发布版本。

## 开发

```powershell
python -m pip install -r requirements-dev.txt
python tools/bootstrap.py
python tools/generate_resources.py
python tools/check_assets.py
.\gradlew.bat runGameTestServer
.\gradlew.bat build runAssetReview
python tools/package_release.py
```

`tools/culinary_catalogue.py`定义效果搭配与说明，`effect/MealCombatEvents.java`实现行为。官方固定版本依赖在`libs/`，验证SHA-512，不打入发布jar。开发验证代码和测试结构不打入发布jar。

新增素材导出：`tools/export_new_assets.cjs`；旧图集导出：`tools/export_textures.cjs`。导出依赖Node.js和sharp，素材检查脚本核对尺寸、调色板、居中及资源引用。

参考：[Farmer's Delight](https://github.com/vectorwing/FarmersDelight/tree/1.21)、[Nether's Delight](https://github.com/Chefs-Delight/NethersDelight_Forge)、[Ocean's Delight](https://github.com/Scouter456/Oceans_Delight)。本项目基于 MIT 协议开源，代码与原创素材均使用 MIT 许可证，前置模组属于各自作者。
