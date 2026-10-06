package com.suiyi.bossesrisedelight.effect;

import com.suiyi.bossesrisedelight.BossesRiseDelight;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.DeferredRegister;
import java.util.List;

public final class CulinaryEffects {
    public static final DeferredRegister<MobEffect> EFFECTS = DeferredRegister.create(Registries.MOB_EFFECT, BossesRiseDelight.MOD_ID);
    public static final RegistryObject<MobEffect> EMBER_APPETITE = trait("ember_appetite", 0xF36B38);
    public static final RegistryObject<MobEffect> BLAZE_DIGEST = trait("blaze_digest", 0xEBA347);
    public static final RegistryObject<MobEffect> FROST_SHELL = trait("frost_shell", 0x94D3EF);
    public static final RegistryObject<MobEffect> FROST_REPRISAL = trait("frost_reprisal", 0xC2E9F1);
    public static final RegistryObject<MobEffect> SAND_SURGE = trait("sand_surge", 0xD8AE62);
    public static final RegistryObject<MobEffect> VENOM_SAC = trait("venom_sac", 0x90AB56);
    public static final RegistryObject<MobEffect> TIDAL_ECHO = trait("tidal_echo", 0x52BCBF);
    public static final RegistryObject<MobEffect> ABYSS_GILLS = trait("abyss_gills", 0x719FB7);
    public static final RegistryObject<MobEffect> SOUL_HARVEST = trait("soul_harvest", 0x68C6BD);
    public static final RegistryObject<MobEffect> NETHER_RESOLVE = trait("nether_resolve", 0xA8717A);
    public static final RegistryObject<MobEffect> HUNTER_RESONANCE = trait("hunter_resonance", 0x9ABD75);
    public static final RegistryObject<MobEffect> RIMEBOUND = EFFECTS.register("rimebound", () ->
            new TraitEffect(MobEffectCategory.HARMFUL, 0x9DD5DD)
                    .addAttributeModifier(Attributes.MOVEMENT_SPEED, "8bdc9dc2-9978-4f05-8fe1-e03568937e6a", -0.18, AttributeModifier.Operation.MULTIPLY_TOTAL));
    public static final RegistryObject<MobEffect> CORROSIVE_VENOM = EFFECTS.register("corrosive_venom", () ->
            new CorrosiveVenomEffect().addAttributeModifier(Attributes.ARMOR, "63c0e49e-87a3-4f16-a9c9-e73eabf69b10", -0.12, AttributeModifier.Operation.MULTIPLY_TOTAL));

    public static final List<RegistryObject<MobEffect>> BENEFICIAL = List.of(EMBER_APPETITE, BLAZE_DIGEST, FROST_SHELL,
            FROST_REPRISAL, SAND_SURGE, VENOM_SAC, TIDAL_ECHO, ABYSS_GILLS, SOUL_HARVEST, NETHER_RESOLVE, HUNTER_RESONANCE);

    private static RegistryObject<MobEffect> trait(String name, int color) {
        return EFFECTS.register(name, () -> new TraitEffect(MobEffectCategory.BENEFICIAL, color));
    }
    private static class TraitEffect extends MobEffect {
        protected TraitEffect(MobEffectCategory category, int color) { super(category, color); }
    }
    private static final class CorrosiveVenomEffect extends MobEffect {
        private CorrosiveVenomEffect() { super(MobEffectCategory.HARMFUL, 0xA2A34D); }
        @Override
        public boolean isDurationEffectTick(int duration, int amplifier) { return duration % 20 == 0; }
        @Override
        public void applyEffectTick(LivingEntity target, int amplifier) {
            if (!target.level().isClientSide) MealCombatEvents.corrosiveTick(target, amplifier);
        }
    }
    private CulinaryEffects() {}
}
