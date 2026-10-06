package com.suiyi.bossesrisedelight.verification;

import com.suiyi.bossesrisedelight.*;
import com.suiyi.bossesrisedelight.effect.CulinaryEffects;
import com.suiyi.bossesrisedelight.effect.MealCombatEvents;
import com.suiyi.bossesrisedelight.item.HuntingMealItem;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.effect.MobEffects;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import net.minecraftforge.items.ItemStackHandler;
import net.minecraftforge.items.wrapper.RecipeWrapper;
import vectorwing.farmersdelight.common.block.FeastBlock;
import vectorwing.farmersdelight.common.crafting.CookingPotRecipe;
import vectorwing.farmersdelight.common.crafting.CuttingBoardRecipe;

import java.util.ArrayList;
import java.util.List;

/** Development-only integration tests, deliberately excluded from the release jar. */
@GameTestHolder(BossesRiseDelight.MOD_ID)
@PrefixGameTestTemplate(false)
public final class DelightGameTests {
    @GameTest(template = "empty")
    public static void recipesLoadAndMatch(GameTestHelper helper) {
        var manager = helper.getLevel().getRecipeManager();
        long count = manager.getRecipes().stream().filter(r -> r.getId().getNamespace().equals(BossesRiseDelight.MOD_ID)).count();
        helper.assertTrue(count == 31, "All 31 addon recipes must parse; loaded " + count);
        helper.assertTrue(manager.byKey(BossesRiseDelight.id("cutting/hunters_feast")).isEmpty(), "Feast cutting must not create free bowls");
        helper.assertTrue(manager.byKey(BossesRiseDelight.id("cutting/kraken_hotpot")).isEmpty(), "Hotpot cutting must not create free bowls");
        var cutHolder = manager.byKey(BossesRiseDelight.id("cutting/clean_sandworm")).orElseThrow();
        var cutting = (CuttingBoardRecipe) cutHolder;
        var cuttingInventory = new ItemStackHandler(2);
        cuttingInventory.setStackInSlot(0, DelightItems.RAW_SANDWORM_FILLET.get().getDefaultInstance());
        cuttingInventory.setStackInSlot(1, DelightItems.KRAKENTOOTH_KNIFE.get().getDefaultInstance());
        var input = new RecipeWrapper(cuttingInventory);
        helper.assertTrue(cutting.matches(input, helper.getLevel()), "Our knife must work in Farmer's Delight cutting recipes");
        ItemStack cleaned = cutting.assemble(input, helper.getLevel().registryAccess());
        helper.assertTrue(cleaned.is(DelightItems.PURIFIED_SANDWORM_FILLET.get()) && cleaned.getCount() == 2, "Cutting must produce two cleaned portions");
        var pot = (CookingPotRecipe) manager.byKey(BossesRiseDelight.id("cooking/kraken_chowder")).orElseThrow();
        var inventory = new ItemStackHandler(6);
        inventory.setStackInSlot(0, DelightItems.RAW_KRAKEN_TENTACLE.get().getDefaultInstance());
        inventory.setStackInSlot(1, new ItemStack(Items.POTATO));
        inventory.setStackInSlot(2, new ItemStack(Items.BROWN_MUSHROOM));
        inventory.setStackInSlot(3, new ItemStack(Items.KELP));
        helper.assertTrue(pot.matches(new RecipeWrapper(inventory), helper.getLevel()), "Chowder ingredients must match the cooking pot");
        helper.assertTrue(pot.getOutputContainer().is(Items.BOWL), "The cooking pot must require the correct serving container");
        var nether = (CookingPotRecipe) manager.byKey(BossesRiseDelight.id("cooking/soul_braised_meat")).orElseThrow();
        inventory.setStackInSlot(0, DelightItems.SOUL_SALT.get().getDefaultInstance());
        inventory.setStackInSlot(1, new ItemStack(Items.BEEF));
        inventory.setStackInSlot(2, new ItemStack(Items.POTATO));
        inventory.setStackInSlot(3, new ItemStack(Items.BROWN_MUSHROOM));
        helper.assertTrue(nether.matches(new RecipeWrapper(inventory), helper.getLevel()), "Nether Knight stew must match real ingredients and common beef tags");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void stackedMealReturnsBowlAndAppliesEffects(GameTestHelper helper) {
        Player player = helper.makeMockSurvivalPlayer();
        player.getFoodData().setFoodLevel(0);
        ItemStack meals = new ItemStack(DelightItems.KRAKEN_CHOWDER.get(), 2);
        player.setItemInHand(InteractionHand.MAIN_HAND, meals);
        ItemStack remaining = meals.finishUsingItem(helper.getLevel(), player);
        helper.assertTrue(remaining.getCount() == 1, "Only one meal should be consumed from a stack");
        helper.assertTrue(player.getInventory().countItem(Items.BOWL) == 1, "A stacked meal must return exactly one bowl");
        helper.assertTrue(player.hasEffect(CulinaryEffects.ABYSS_GILLS.get()), "Chowder must grant its original culinary effect");
        helper.assertTrue(!player.hasEffect(MobEffects.WATER_BREATHING), "Chowder must not be a renamed vanilla water-breathing potion");
        helper.assertTrue(player.getFoodData().getFoodLevel() == 10, "Chowder must restore ten hunger points");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void feastServesFourAndCannotResetByBreaking(GameTestHelper helper) {
        BlockPos pos = new BlockPos(2, 1, 2);
        helper.setBlock(pos.below(), Blocks.STONE);
        helper.setBlock(pos, DelightBlocks.HUNTERS_FEAST.get());
        Player player = helper.makeMockSurvivalPlayer();
        helper.useBlock(pos, player);
        helper.assertBlockProperty(pos, FeastBlock.SERVINGS, 4);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.BOWL, 4));
        for (int i = 0; i < 4; i++) {
            helper.useBlock(pos, player);
            helper.assertBlockProperty(pos, FeastBlock.SERVINGS, 3 - i);
        }
        helper.assertTrue(player.getInventory().countItem(DelightItems.HUNTERS_FEAST_SERVING.get()) == 4, "Feast must provide exactly four portions");
        var leftovers = Block.getDrops(helper.getBlockState(pos), helper.getLevel(), helper.absolutePos(pos), null);
        helper.assertTrue(leftovers.stream().noneMatch(s -> s.is(DelightItems.HUNTERS_FEAST.get())), "Breaking a used feast must not return a fresh feast");
        helper.assertTrue(leftovers.stream().mapToInt(s -> s.is(Items.BOWL) ? s.getCount() : 0).sum() == 1, "Empty platter returns one bowl");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void additiveLootAndKnifeBonus(GameTestHelper helper) {
        Player player = helper.makeMockSurvivalPlayer();
        String[] bosses = {"infernal_dragon", "yeti", "sandworm", "kraken", "underworld_knight"};
        Item[] ingredients = {DelightItems.RAW_DRAGON_CUT.get(), DelightItems.RAW_YETI_CUT.get(),
                DelightItems.RAW_SANDWORM_FILLET.get(), DelightItems.RAW_KRAKEN_TENTACLE.get(), DelightItems.NETHER_EMBER.get()};
        for (int i = 0; i < bosses.length; i++) {
            ResourceLocation entityId = new ResourceLocation("block_factorys_bosses", bosses[i]);
            Entity boss = BuiltInRegistries.ENTITY_TYPE.get(entityId).create(helper.getLevel());
            helper.assertTrue(boss != null, "Boss entity must be registered: " + entityId);
            LootTable table = helper.getLevel().getServer().getLootData().getLootTable(new ResourceLocation("block_factorys_bosses", "entities/" + bosses[i]));
            var params = lootParams(helper, boss, player);
            List<ItemStack> base = new ArrayList<>();
            table.getRandomItemsRaw(params, base::add);
            helper.assertTrue(!base.isEmpty(), "Original boss drops must be present");
            var originalWeaponLoot = table.getRandomItems(params, 417L);
            Item food = ingredients[i];
            int normalAmount = originalWeaponLoot.stream().filter(s -> s.is(food)).mapToInt(ItemStack::getCount).sum();
            helper.assertTrue(normalAmount >= 6 && normalAmount <= 10, "Boss must add 6-10 ingredients: " + bosses[i]);
            for (ItemStack original : base) helper.assertTrue(originalWeaponLoot.stream().anyMatch(s -> s.is(original.getItem())), "Addon must retain original loot");
            player.setItemInHand(InteractionHand.MAIN_HAND, DelightItems.KRAKENTOOTH_KNIFE.get().getDefaultInstance());
            var knifeLoot = table.getRandomItems(params, 417L);
            int knifeAmount = knifeLoot.stream().filter(s -> s.is(food)).mapToInt(ItemStack::getCount).sum();
            helper.assertTrue(knifeAmount == normalAmount + 2, "Knife must add exactly two bonus ingredients");
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            var withoutPlayer = table.getRandomItems(lootParams(helper, boss, null), 417L);
            helper.assertTrue(withoutPlayer.stream().noneMatch(s -> s.is(food)), "Non-player kills must not receive extra ingredients");
        }
        helper.succeed();
    }

    private static LootParams lootParams(GameTestHelper helper, Entity boss, Player player) {
        return new LootParams.Builder(helper.getLevel())
                .withParameter(LootContextParams.THIS_ENTITY, boss)
                .withParameter(LootContextParams.ORIGIN, boss.position())
                .withParameter(LootContextParams.DAMAGE_SOURCE, player == null ? helper.getLevel().damageSources().generic() : helper.getLevel().damageSources().playerAttack(player))
                .withOptionalParameter(LootContextParams.LAST_DAMAGE_PLAYER, player)
                .create(LootContextParamSets.ENTITY);
    }

    @GameTest(template = "empty")
    public static void everyCookedMealHasOriginalEffectsAndWorksAtFullHunger(GameTestHelper helper) {
        Player p = actor(helper);
        int customFoods = 0;
        for (var item : DelightItems.ALL) {
            if (!(item.get() instanceof HuntingMealItem meal) || meal.bonuses().isEmpty()) continue;
            customFoods++;
            ItemStack stack = meal.getDefaultInstance();
            helper.assertTrue(stack.getFoodProperties(p).canAlwaysEat(), "Custom battle meals must work at full hunger");
            helper.assertTrue(stack.getFoodProperties(p).getEffects().isEmpty(), "Positive battle effects must be custom mechanics, not vanilla potion lists");
        }
        helper.assertTrue(customFoods == 21, "All 21 processed foods and meals need custom effects; found " + customFoods);
        p.getFoodData().setFoodLevel(20);
        var bowl = new ItemStack(DelightItems.SOUL_BRAISED_MEAT.get());
        p.setItemInHand(InteractionHand.MAIN_HAND, bowl);
        helper.assertTrue(bowl.use(helper.getLevel(), p, InteractionHand.MAIN_HAND).getResult().consumesAction(), "A full player must be able to begin eating a battle meal");
        ItemStack remainder = bowl.finishUsingItem(helper.getLevel(), p);
        helper.assertTrue(remainder.is(Items.BOWL) && p.hasEffect(CulinaryEffects.SOUL_HARVEST.get()), "Nether meal must grant Soul Harvest and return its bowl");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void bothFeastsConserveFiveBowlsThroughServingAndEating(GameTestHelper helper) {
        Player p = actor(helper);
        FeastBlock[] blocks = {DelightBlocks.HUNTERS_FEAST.get(), DelightBlocks.KRAKEN_HOTPOT.get()};
        Item[] foods = {DelightItems.HUNTERS_FEAST_SERVING.get(), DelightItems.KRAKEN_HOTPOT_SERVING.get()};
        for (int index = 0; index < 2; index++) {
            Item serving = foods[index];
            p.getInventory().clearContent();
            BlockPos pos = new BlockPos(2, 1, 2);
            helper.setBlock(pos.below(), Blocks.STONE);
            helper.setBlock(pos, blocks[index]);
            // One bowl is already in the crafted platter, plus four bowls for the portions.
            p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.BOWL, 4));
            for (int i = 0; i < 4; i++) helper.useBlock(pos, p);
            helper.assertTrue(p.getInventory().countItem(Items.BOWL) == 0, "Taking portions must consume four actual bowls");
            var stacks = p.getInventory().items.stream().filter(s -> s.is(serving)).toList();
            for (ItemStack portions : stacks) while (!portions.isEmpty()) {
                ItemStack remainder = portions.finishUsingItem(helper.getLevel(), p);
                if (remainder.is(Items.BOWL)) p.getInventory().add(remainder);
            }
            helper.assertTrue(p.getInventory().countItem(Items.BOWL) == 4, "Eating must return exactly the four portion bowls");
            Block.getDrops(helper.getBlockState(pos), helper.getLevel(), helper.absolutePos(pos), null).forEach(p.getInventory()::add);
            helper.assertTrue(p.getInventory().countItem(Items.BOWL) == 5, "Crafting, serving, eating and cleanup must conserve five bowls");
        }
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void emberComboDetonatesAndDoesNotRecursivelyChain(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.EMBER_APPETITE.get(), 400));
        Mob target = durableTarget(helper);
        float before = target.getHealth();
        for (int i = 0; i < 3; i++) { target.invulnerableTime = 0; target.hurt(helper.getLevel().damageSources().playerAttack(p), 1); }
        helper.assertTrue(Math.abs(before - target.getHealth() - 7) < .01, "Three 1-damage hits must add exactly one 4-damage burst");
        helper.runAfterDelay(15, () -> {
            helper.assertTrue(Math.abs(before - target.getHealth() - 7) < .01, "A culinary burst must not create further delayed or recursive damage");
            helper.succeed();
        });
    }

    @GameTest(template = "empty")
    public static void blazeDigestReducesFireAndRestoresHealth(GameTestHelper helper) {
        Player p = actor(helper);
        p.setHealth(10);
        p.addEffect(new MobEffectInstance(CulinaryEffects.BLAZE_DIGEST.get(), 400));
        p.hurt(helper.getLevel().damageSources().inFire(), 10);
        helper.assertTrue(Math.abs(p.getHealth() - 7.5F) < .01, "Ten fire damage should become four, followed by 1.5 healing");
        p.invulnerableTime = 0;
        p.hurt(helper.getLevel().damageSources().inFire(), 10);
        helper.assertTrue(Math.abs(p.getHealth() - 3.5F) < .01, "Fire healing must respect its cooldown");
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 180)
    public static void frostShellAbsorbsAndRebuildsAfterQuietPeriod(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.FROST_SHELL.get(), 600));
        Mob enemy = helper.spawn(EntityType.ZOMBIE, new BlockPos(2, 1, 2));
        enemy.setNoAi(true);
        // Generic damage stays four points even when the test world uses Easy difficulty.
        p.hurt(helper.getLevel().damageSources().generic(), 4);
        helper.assertTrue(p.getHealth() == 20, "Frost Shell must absorb the first four health damage");
        helper.assertTrue(enemy.hasEffect(CulinaryEffects.RIMEBOUND.get()), "A shattered shell must release chilling mist");
        p.invulnerableTime = 0;
        p.hurt(helper.getLevel().damageSources().generic(), 1);
        helper.assertTrue(p.getHealth() == 19, "A spent shield must not instantly refill");
        helper.runAfterDelay(121, () -> {
            MealCombatEvents.updateEntity(p);
            helper.assertTrue(MealCombatEvents.frostShield(p) == 4, "The shield must rebuild after six quiet seconds");
            helper.succeed();
        });
    }

    @GameTest(template = "empty")
    public static void frostReprisalCountersOnlyOncePerCooldown(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.FROST_REPRISAL.get(), 400));
        Mob attacker = durableTarget(helper);
        float before = attacker.getHealth();
        p.hurt(helper.getLevel().damageSources().mobAttack(attacker), 2);
        helper.assertTrue(Math.abs(before - attacker.getHealth() - 3) < .01 && attacker.hasEffect(CulinaryEffects.RIMEBOUND.get()), "Counter must deal three damage and apply original frost debuff");
        p.invulnerableTime = 0;
        p.hurt(helper.getLevel().damageSources().mobAttack(attacker), 2);
        helper.assertTrue(Math.abs(before - attacker.getHealth() - 3) < .01, "Repeated hits during cooldown must not repeat the counter");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void sandSurgeArmsOneStrikeAndRespectsCooldown(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.SAND_SURGE.get(), 400));
        p.setOnGround(true);
        p.setSprinting(true);
        MealCombatEvents.updateEntity(p);
        helper.assertTrue(p.getDeltaMovement().horizontalDistanceSqr() > .4, "Sprint start must create a real movement burst");
        Mob target = durableTarget(helper);
        float before = target.getHealth();
        target.hurt(helper.getLevel().damageSources().playerAttack(p), 1);
        helper.assertTrue(Math.abs(before - target.getHealth() - 4) < .01, "Surge must add three damage to one melee strike");
        target.invulnerableTime = 0;
        target.hurt(helper.getLevel().damageSources().playerAttack(p), 1);
        helper.assertTrue(Math.abs(before - target.getHealth() - 5) < .01, "The armed strike must be consumed after one hit");
        p.setSprinting(false); MealCombatEvents.updateEntity(p);
        p.setDeltaMovement(Vec3.ZERO);
        p.setSprinting(true); MealCombatEvents.updateEntity(p);
        helper.assertTrue(p.getDeltaMovement().lengthSqr() == 0, "Toggling sprint must not bypass the movement cooldown");
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 80)
    public static void venomInflictsOriginalDamageOverTime(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.VENOM_SAC.get(), 400));
        Mob target = durableTarget(helper);
        float before = target.getHealth();
        target.hurt(helper.getLevel().damageSources().playerAttack(p), 1);
        helper.assertTrue(target.hasEffect(CulinaryEffects.CORROSIVE_VENOM.get()) && !target.hasEffect(MobEffects.POISON), "Venom must apply its original effect rather than vanilla poison");
        helper.runAfterDelay(25, () -> {
            helper.assertTrue(before - target.getHealth() >= 2, "The original poison must actually tick for damage");
            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 60)
    public static void tidalEchoStrikesOnceAfterDelay(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.TIDAL_ECHO.get(), 400));
        Mob target = durableTarget(helper);
        float before = target.getHealth();
        target.hurt(helper.getLevel().damageSources().playerAttack(p), 1);
        helper.assertTrue(before - target.getHealth() == 1, "The echo must not deal damage immediately");
        helper.runAfterDelay(15, () -> {
            helper.assertTrue(Math.abs(before - target.getHealth() - 3) < .01, "After 0.6 seconds one two-damage echo must arrive");
            helper.runAfterDelay(15, () -> {
                helper.assertTrue(Math.abs(before - target.getHealth() - 3) < .01, "An echo must not schedule another echo");
                helper.succeed();
            });
        });
    }

    @GameTest(template = "empty")
    public static void soulHarvestGuardsOneLethalHitAndConsumesSouls(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.SOUL_HARVEST.get(), 400));
        gatherSouls(helper, p);
        helper.assertTrue(MealCombatEvents.warSouls(p) == 3, "Three hostile kills must collect three souls");
        p.hurt(helper.getLevel().damageSources().generic(), 50);
        helper.assertTrue(p.isAlive() && p.getHealth() == 1, "Three souls must protect one lethal hit at one health");
        helper.assertTrue(!p.hasEffect(CulinaryEffects.SOUL_HARVEST.get()) && MealCombatEvents.warSouls(p) == 0, "The protection must consume the effect and all souls");
        p.invulnerableTime = 0;
        p.hurt(helper.getLevel().damageSources().generic(), 10);
        helper.assertTrue(!p.isAlive(), "Soul protection must not grant unlimited survival");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void soulGuardAccountsForAbsorptionHearts(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.SOUL_HARVEST.get(), 400));
        gatherSouls(helper, p);
        p.setAbsorptionAmount(4);
        p.setHealth(10);
        p.hurt(helper.getLevel().damageSources().generic(), 12);
        helper.assertTrue(p.getHealth() == 2 && MealCombatEvents.warSouls(p) == 3, "Absorption must prevent spending souls on a nonlethal hit");
        p.invulnerableTime = 0;
        p.hurt(helper.getLevel().damageSources().generic(), 8);
        helper.assertTrue(p.isAlive() && p.getHealth() == 1 && MealCombatEvents.warSouls(p) == 0, "The next truly lethal hit must consume the souls correctly");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void netherResolveTurnsLowHealthDamageIntoCounterWindow(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.NETHER_RESOLVE.get(), 400));
        p.setHealth(7);
        p.hurt(helper.getLevel().damageSources().generic(), 1);
        Mob target = durableTarget(helper);
        float before = target.getHealth();
        target.hurt(helper.getLevel().damageSources().playerAttack(p), 1);
        helper.assertTrue(Math.abs(before - target.getHealth() - 5) < .01 && p.getHealth() == 8, "Low-health counter must add four damage and restore two health");
        target.invulnerableTime = 0;
        target.hurt(helper.getLevel().damageSources().playerAttack(p), 1);
        helper.assertTrue(Math.abs(before - target.getHealth() - 6) < .01, "Counter window must be consumed after one attack");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void hunterResonanceRewardsHostileKillsOnly(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.HUNTER_RESONANCE.get(), 400));
        p.setHealth(10);
        Mob hostile = helper.spawn(EntityType.ZOMBIE, new BlockPos(2, 1, 2));
        hostile.hurt(helper.getLevel().damageSources().playerAttack(p), 100);
        helper.assertTrue(p.getHealth() == 12, "A hostile kill must restore two health");
        Mob cow = durableTarget(helper);
        cow.hurt(helper.getLevel().damageSources().playerAttack(p), 100);
        helper.assertTrue(p.getHealth() == 12, "Passive animals must not feed the hostile-kill healing loop");
        helper.succeed();
    }

    private static Player actor(GameTestHelper helper) {
        Player p = helper.makeMockSurvivalPlayer();
        p.moveTo(helper.absoluteVec(new Vec3(1, 1, 1)));
        return p;
    }
    @GameTest(template = "empty", timeoutTicks = 80)
    public static void abyssGillsTradesAirForDefenseAndReplenishesAir(GameTestHelper helper) {
        Mob target = durableTarget(helper);
        target.setNoGravity(true);
        for (int x = 1; x <= 3; x++) for (int z = 1; z <= 3; z++) {
            helper.setBlock(x, 1, z, Blocks.WATER);
            helper.setBlock(x, 2, z, Blocks.WATER);
        }
        target.addEffect(new MobEffectInstance(CulinaryEffects.ABYSS_GILLS.get(), 400));
        helper.runAfterDelay(3, () -> {
            helper.assertTrue(target.isInWater(), "Fixture must be in actual water");
            target.setAirSupply(160);
            float before = target.getHealth();
            target.hurt(helper.getLevel().damageSources().generic(), 10);
            helper.assertTrue(Math.abs(before - target.getHealth() - 6.5F) < .01 && target.getAirSupply() == 80, "Gills must spend 80 air to reduce this hit by 35%");
            target.invulnerableTime = 0;
            target.hurt(helper.getLevel().damageSources().generic(), 10);
            helper.assertTrue(Math.abs(before - target.getHealth() - 16.5F) < .01 && target.getAirSupply() == 80, "The air shield must respect its five-second cooldown");
            target.setAirSupply(5);
            helper.runAfterDelay(23, () -> {
                helper.assertTrue(target.getAirSupply() > 5, "Gills must replenish real air underwater");
                helper.succeed();
            });
        });
    }
    @GameTest(template = "empty")
    public static void offensiveProcsDoNotHurtOtherPlayersByDefault(GameTestHelper helper) {
        Player attacker = actor(helper), target = actor(helper);
        attacker.addEffect(new MobEffectInstance(CulinaryEffects.EMBER_APPETITE.get(), 400));
        attacker.addEffect(new MobEffectInstance(CulinaryEffects.VENOM_SAC.get(), 400));
        attacker.addEffect(new MobEffectInstance(CulinaryEffects.TIDAL_ECHO.get(), 400));
        for (int i = 0; i < 3; i++) { target.invulnerableTime = 0; target.hurt(helper.getLevel().damageSources().playerAttack(attacker), 1); }
        helper.assertTrue(target.getHealth() == 17 && !target.hasEffect(CulinaryEffects.CORROSIVE_VENOM.get()), "Default settings must preserve normal attacks without offensive food procs against players");
        helper.succeed();
    }
    @GameTest(template = "empty")
    public static void soulGuardDoesNotPreventVoidDeath(GameTestHelper helper) {
        Player p = actor(helper);
        p.addEffect(new MobEffectInstance(CulinaryEffects.SOUL_HARVEST.get(), 400));
        gatherSouls(helper, p);
        p.hurt(helper.getLevel().damageSources().fellOutOfWorld(), 100);
        helper.assertTrue(!p.isAlive(), "Void and invulnerability-bypassing damage must retain their original behavior");
        helper.succeed();
    }
    private static Mob durableTarget(GameTestHelper helper) {
        helper.setBlock(2, 0, 2, Blocks.STONE);
        Mob target = helper.spawn(EntityType.COW, new BlockPos(2, 1, 2));
        target.setNoAi(true);
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(80);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(80);
        return target;
    }

    @GameTest(template = "empty")
    public static void forgeRollCapabilityArmsSandSurge(GameTestHelper helper) {
        Player player = actor(helper);
        player.addEffect(new MobEffectInstance(CulinaryEffects.SAND_SURGE.get(), 400));
        player.setOnGround(true);
        var roll = net.unusual.block_factorys_bosses.capability.entity.RollCap.fromPlayer(player).orElseThrow();
        // A newly attached Forge capability begins in its five-tick initialization delay.
        for (int tick = 0; tick < 6; tick++) roll.tick(player);
        helper.assertTrue(roll.startRoll(player, 0, 1) && roll.isRolling(), "Bosses'Rise Forge roll capability must start a real roll");
        MealCombatEvents.updateEntity(player);
        Mob target = durableTarget(helper);
        float before = target.getHealth();
        target.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
        helper.assertTrue(Math.abs(before - target.getHealth() - 4) < .01, "A Forge roll must arm the three-damage sand strike");
        target.invulnerableTime = 0;
        target.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
        helper.assertTrue(Math.abs(before - target.getHealth() - 5) < .01, "A roll must arm only one strike");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void fireHealingWorksAtFullHealthOnForge(GameTestHelper helper) {
        Player player = actor(helper);
        player.addEffect(new MobEffectInstance(CulinaryEffects.BLAZE_DIGEST.get(), 400));
        player.hurt(helper.getLevel().damageSources().inFire(), 10);
        helper.assertTrue(Math.abs(player.getHealth() - 17.5F) < .01, "Full-health fire defense must reduce damage and restore 1.5 health");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void fireHealingCannotRescueAnAlreadyLethalHit(GameTestHelper helper) {
        Player player = actor(helper);
        player.setHealth(1);
        player.addEffect(new MobEffectInstance(CulinaryEffects.BLAZE_DIGEST.get(), 400));
        player.hurt(helper.getLevel().damageSources().inFire(), 10);
        helper.assertTrue(!player.isAlive(), "Fire healing must not replace the Soul Harvest lethal guard");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void forgeKnifeTagRewardsFarmersDelightKnives(GameTestHelper helper) {
        Player player = actor(helper);
        Entity boss = BuiltInRegistries.ENTITY_TYPE.get(new ResourceLocation("block_factorys_bosses", "yeti")).create(helper.getLevel());
        LootTable table = helper.getLevel().getServer().getLootData().getLootTable(new ResourceLocation("block_factorys_bosses", "entities/yeti"));
        var params = lootParams(helper, boss, player);
        int baseline = table.getRandomItems(params, 819L).stream().filter(s -> s.is(DelightItems.RAW_YETI_CUT.get())).mapToInt(ItemStack::getCount).sum();
        player.setItemInHand(InteractionHand.MAIN_HAND, vectorwing.farmersdelight.common.registry.ModItems.IRON_KNIFE.get().getDefaultInstance());
        int withKnife = table.getRandomItems(params, 819L).stream().filter(s -> s.is(DelightItems.RAW_YETI_CUT.get())).mapToInt(ItemStack::getCount).sum();
        helper.assertTrue(withKnife == baseline + 2, "Forge common knife tags must reward Farmer's Delight's own knives");
        helper.succeed();
    }

    @GameTest(template = "empty")
    public static void forgeSurgeDamageStillPassesThroughArmor(GameTestHelper helper) {
        Player player = actor(helper);
        player.addEffect(new MobEffectInstance(CulinaryEffects.SAND_SURGE.get(), 400));
        player.setOnGround(true);
        player.setSprinting(true);
        MealCombatEvents.updateEntity(player);
        Mob target = durableTarget(helper);
        target.getAttribute(Attributes.ARMOR).setBaseValue(20);
        float before = target.getHealth();
        target.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
        float lost = before - target.getHealth();
        helper.assertTrue(lost > 0 && lost < 2, "The melee bonus must pass through Forge armor mitigation rather than bypass it");
        helper.succeed();
    }
    private static void gatherSouls(GameTestHelper helper, Player player) {
        for (int i = 0; i < 3; i++) {
            Mob target = helper.spawn(EntityType.ZOMBIE, new BlockPos(2, 1, 2));
            target.hurt(helper.getLevel().damageSources().playerAttack(player), 100);
        }
    }
}
