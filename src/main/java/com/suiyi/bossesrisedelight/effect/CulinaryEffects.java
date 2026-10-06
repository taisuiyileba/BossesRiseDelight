package com.suiyi.bossesrisedelight.effect;

import com.suiyi.bossesrisedelight.BossesRiseDelight;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import java.util.List;

public final class CulinaryEffects {
    public static final DeferredRegister<MobEffect> EFFECTS = DeferredRegister.create(Registries.MOB_EFFECT, BossesRiseDelight.MOD_ID);
    public static final DeferredHolder<MobEffect, MobEffect> EMBER_APPETITE = trait("ember_appetite", 0xF36B38);
    public static final DeferredHolder<MobEffect, MobEffect> BLAZE_DIGEST = trait("blaze_digest", 0xEBA347);
    public static final DeferredHolder<MobEffect, MobEffect> FROST_SHELL = trait("frost_shell", 0x94D3EF);
    public static final DeferredHolder<MobEffect, MobEffect> FROST_REPRISAL = trait("frost_reprisal", 0xC2E9F1);
    public static final DeferredHolder<MobEffect, MobEffect> SAND_SURGE = trait("sand_surge", 0xD8AE62);
    public static final DeferredHolder<MobEffect, MobEffect> VENOM_SAC = trait("venom_sac", 0x90AB56);
    public static final DeferredHolder<MobEffect, MobEffect> TIDAL_ECHO = trait("tidal_echo", 0x52BCBF);
    public static final DeferredHolder<MobEffect, MobEffect> ABYSS_GILLS = trait("abyss_gills", 0x719FB7);
    public static final DeferredHolder<MobEffect, MobEffect> SOUL_HARVEST = trait("soul_harvest", 0x68C6BD);
    public static final DeferredHolder<MobEffect, MobEffect> NETHER_RESOLVE = trait("nether_resolve", 0xA8717A);
    public static final DeferredHolder<MobEffect, MobEffect> HUNTER_RESONANCE = trait("hunter_resonance", 0x9ABD75);
    public static final DeferredHolder<MobEffect, MobEffect> RIMEBOUND = EFFECTS.register("rimebound", () ->
            new TraitEffect(MobEffectCategory.HARMFUL, 0x9DD5DD)
                    .addAttributeModifier(Attributes.MOVEMENT_SPEED, BossesRiseDelight.id("rimebound_stride"), -0.18, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
    public static final DeferredHolder<MobEffect, MobEffect> CORROSIVE_VENOM = EFFECTS.register("corrosive_venom", () ->
            new CorrosiveVenomEffect().addAttributeModifier(Attributes.ARMOR, BossesRiseDelight.id("venom_armor"), -0.12, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));

    public static final List<DeferredHolder<MobEffect, MobEffect>> BENEFICIAL = List.of(EMBER_APPETITE, BLAZE_DIGEST, FROST_SHELL,
            FROST_REPRISAL, SAND_SURGE, VENOM_SAC, TIDAL_ECHO, ABYSS_GILLS, SOUL_HARVEST, NETHER_RESOLVE, HUNTER_RESONANCE);

    private static DeferredHolder<MobEffect, MobEffect> trait(String name, int color) {
        return EFFECTS.register(name, () -> new TraitEffect(MobEffectCategory.BENEFICIAL, color));
    }
    private static class TraitEffect extends MobEffect {
        protected TraitEffect(MobEffectCategory category, int color) { super(category, color); }
    }
    private static final class CorrosiveVenomEffect extends MobEffect {
        private CorrosiveVenomEffect() { super(MobEffectCategory.HARMFUL, 0xA2A34D); }
        @Override
        public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) { return duration % 20 == 0; }
        @Override
        public boolean applyEffectTick(LivingEntity target, int amplifier) {
            if (!target.level().isClientSide) MealCombatEvents.corrosiveTick(target, amplifier);
            return true;
        }
    }
    private CulinaryEffects() {}
}
