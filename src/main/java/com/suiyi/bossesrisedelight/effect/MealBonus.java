package com.suiyi.bossesrisedelight.effect;

import com.suiyi.bossesrisedelight.DelightConfig;
import java.util.function.Supplier;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;

public record MealBonus(Supplier<MobEffect> effect, int seconds, int amplifier) {
    public MobEffectInstance instance() {
        return new MobEffectInstance(effect.get(), Math.max(20, (int) (seconds * 20 * DelightConfig.durationScale())), amplifier);
    }
}
