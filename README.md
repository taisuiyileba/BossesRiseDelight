# Bosses'Rise Delight / 首领乐事

Minecraft **1.20.1** · Forge **47.4.20+（47.x）** · Java **17** · 附属版本 **1.1.0**。

由相邻目录中的 1.21.1 NeoForge 版本移植。保留 25 个食物、2 种冥骑调味材料、2 把厨刀、2 个四人份宴席方块、31 条配方和 13 种原创效果，以及中英文提示、贴图和模型。

## 安装

客户端与服务端均安装 `release/bossesrise-delight-1.20.1-forge-1.1.0.jar`，并安装以下 **1.20.1 Forge** 前置：

- [Bosses'Rise 2.1.2](https://modrinth.com/mod/bossesrise/version/jwkdmnrh)
- [Farmer's Delight 1.20.1-1.3.4](https://modrinth.com/mod/farmers-delight/version/SiIpcZzM)
- [GeckoLib 4.8.3](https://modrinth.com/mod/geckolib/version/HVdLnQMI)

前置单独安装；本附属的 jar 不包含它们。原有 1.21.1 NeoForge 存档不属于本次向下移植的迁移范围。

## 玩法

玩家击败炼狱龙、雪怪、沙虫、克拉肯与冥界骑士时，保留原战利品并追加 6～10 份食材。掉落生成时击杀者主手持有效厨刀，默认额外增加 2 份；农夫乐事自己的厨刀也享有此奖励。

龙肉、雪怪肉、触手可烧炼。沙虫肉先在切菜板上净化，每段获得两份；冥火余烬可研磨为两份灵魂盐。烹饪锅和合成台提供各路线料理；熟食的原创效果支持满饥饿食用。碗装料理吃完返还一个碗，堆叠食用同样返还。

猎人盛宴和克拉肯海鲜火锅各有四份，用碗领取，每份消耗一个实际持有的碗。食用返还四个分餐碗，清理宴席返还其合成时的一只碗；使用过的宴席打破不会重置成新宴席。

龙骨厨刀使用钻石材质且掉落物耐火，克拉肯牙厨刀使用铁材质。两者保留农夫乐事的切菜、蛋糕切片和南瓜雕刻功能。

原创效果包括火爆连击、火伤减免和回血、霜盾与冰牙反击、冲刺及翻滚突击、腐毒、延迟追击、水下补气和耗气防御、战魂护命、低血量反击和友军恢复。完整料理搭配及效果参数见 [docs/custom-effects.md](docs/custom-effects.md)。

## 配置

世界的 `serverconfig/bossesrise_delight-server.toml` 支持：

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

Forge 的餐食防御在护甲和吸收心结算后的最终伤害事件中生效。战魂护命使用剩余生命值判断致命伤，火伤回血使用预期扣血后的生命值计算；近战突击加成仍经过护甲。额外料理伤害不会递归触发进攻效果。翻滚使用 Bosses'Rise Forge 的 `RollCap`，沿用其初始化延迟和冷却。

## 构建与测试

```powershell
python -m pip install -r requirements-dev.txt
python tools/bootstrap.py
python tools/optimize_item_textures.py
python tools/generate_resources.py
python tools/verify.py
python tools/package_release.py
```

构建使用 ForgeGradle 6.0.54、官方 1.20.1 映射和 Java 17。Gradle 可自动解析 Java 17 工具链；前置版本及 SHA-512 固定在 `dependencies.lock.json`。

`optimize_item_textures.py` 从内嵌像素数据重建 29 张物品贴图和 4 张宴席方块贴图，仅需 Pillow，无需旧图集。`generate_resources.py` 同步生成两种宴席各 5 个份数状态的模型，并保留 1.20.1 Forge 的配方和数据目录格式。

`verify.py` 检查素材，构建并重混淆正式 jar，运行 25 项 GameTests，再依次启动三个会自动截图和退出的开发客户端，检查 31 个物品模型、13 个效果图标、8 种厨刀手持视角及两把刀的中文提示。它核对实际测试通过记录，避免把服务器启动失败后的 Gradle 成功退出误判为测试成功。

验证记录保存在 `docs/verification-report.json`，日志在 `build/verification/`。正式 jar 排除验证类和空测试结构；发布工具检查 Java 17 字节码、Forge 元数据、源码与已验证 jar 的哈希。

测试覆盖配方、五种首领掉落与持刀奖励、容器守恒、满饥饿食用、战斗触发与冷却、真实水中补气、吸收心、虚空和默认玩家攻击规则，并增加 Forge 翻滚、通用厨刀标签、护甲结算与火伤回血的回归测试。尚未进行完整生存平衡游玩或多人压力测试。

`tools/test_release_server.py` 还可使用已安装到 `build/production-smoke/` 的官方 Forge 服务端测试正式重混淆 jar。它在该隔离目录内创建测试配置和 EULA 文件，仅监听本机临时端口，自动放置两种宴席、召唤雪怪、施加腐毒、调用原版掉落表、重载数据并关闭服务端。需通过 `--java` 指定 Java 17 可执行文件。结果保存在 `docs/production-server-test.json`；发布工具会核对正式 jar 哈希并合入总报告。

实际客户端截图：[全部物品与效果](docs/in-game-preview.png)、[厨刀手持模型](docs/knife-held-models.png)、[中文厨刀提示](docs/knife-tooltips.png)。

Bosses'Rise 2.1.2 自身的沙虫模型会触发 GeckoLib 几何格式警告；本附属保留官方前置文件及其校验值。

代码及原创素材沿用 MIT 协议，前置模组属于各自作者。

## CurseForge 发布

先完成构建和验证，再运行 `python tools/publish_curseforge.py` 预览本版本的发布内容。加 `--all` 可包含相邻目录中的另一版本，加 `--upload` 执行上传。

通过 `CURSEFORGE_API_TOKEN` 环境变量提供令牌，或用 `--tokens <path>` 读取与 MobSpawnController 发布脚本相同格式的 `api_tokens.json`。令牌文件、发布回执与构建产物不提交到 Git。版本号统一读取 `gradle.properties`，更新日志读取 `CHANGELOG-<版本>.md`。
