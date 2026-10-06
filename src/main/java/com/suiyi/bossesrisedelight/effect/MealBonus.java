package com.suiyi.bossesrisedelight.effect;

import com.suiyi.bossesrisedelight.DelightConfig;
import net.minecraft.core.Holder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;

public record MealBonus(Holder<MobEffect> effect, int seconds, int amplifier) {
    public MobEffectInstance instance() {
        return new MobEffectInstance(effect, Math.max(20, (int) (seconds * 20 * DelightConfig.durationScale())), amplifier);
    }
}
