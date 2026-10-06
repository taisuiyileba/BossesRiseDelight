package com.suiyi.bossesrisedelight;

import net.minecraftforge.common.ForgeConfigSpec;

public final class DelightConfig {
    public static final ForgeConfigSpec SPEC;
    public static final ForgeConfigSpec.BooleanValue INGREDIENT_DROPS;
    public static final ForgeConfigSpec.IntValue DROP_MULTIPLIER;
    public static final ForgeConfigSpec.IntValue KNIFE_BONUS;
    public static final ForgeConfigSpec.BooleanValue MEAL_EFFECTS;
    public static final ForgeConfigSpec.BooleanValue PVP_PROCS;
    public static final ForgeConfigSpec.DoubleValue EFFECT_DURATION_SCALE;
    public static final ForgeConfigSpec.DoubleValue PROC_DAMAGE_SCALE;

    static {
        ForgeConfigSpec.Builder builder = new ForgeConfigSpec.Builder();
        builder.push("hunting");
        INGREDIENT_DROPS = builder.comment("Add boss ingredients alongside the original boss loot. Requires a player kill.")
                .define("ingredientDrops", true);
        DROP_MULTIPLIER = builder.comment("Multiplier for ingredient amounts. Original loot is unaffected.")
                .defineInRange("dropMultiplier", 1, 1, 8);
        KNIFE_BONUS = builder.comment("Extra ingredients when the credited player's main-hand weapon is a knife.")
                .defineInRange("knifeBonus", 2, 0, 16);
        builder.pop();
        builder.push("cuisine");
        MEAL_EFFECTS = builder.comment("Enable the addon's custom meal effects and combat mechanics.").define("customMealEffects", true);
        EFFECT_DURATION_SCALE = builder.comment("Multiplier for custom meal effect durations.").defineInRange("effectDurationScale", 1.0, 0.25, 5.0);
        PROC_DAMAGE_SCALE = builder.comment("Multiplier for triggered culinary damage (normal weapon damage is unchanged).").defineInRange("procDamageScale", 1.0, 0.0, 3.0);
        PVP_PROCS = builder.comment("Allow offensive culinary procs to affect other players. Defensive effects still work.").define("pvpProcs", false);
        builder.pop();
        SPEC = builder.build();
    }

    private DelightConfig() {}
    public static boolean effectsEnabled() { return !SPEC.isLoaded() || MEAL_EFFECTS.get(); }
    public static boolean pvpEnabled() { return SPEC.isLoaded() && PVP_PROCS.get(); }
    public static double durationScale() { return SPEC.isLoaded() ? EFFECT_DURATION_SCALE.get() : 1.0; }
    public static float damageScale() { return SPEC.isLoaded() ? PROC_DAMAGE_SCALE.get().floatValue() : 1.0F; }
}
