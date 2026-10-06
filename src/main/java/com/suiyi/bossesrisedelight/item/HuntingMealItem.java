package com.suiyi.bossesrisedelight.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.effect.MobEffectUtil;
import com.suiyi.bossesrisedelight.DelightConfig;
import com.suiyi.bossesrisedelight.effect.MealBonus;
import vectorwing.farmersdelight.common.item.ConsumableItem;

import java.util.List;

/** Farmer's Delight's consumable handles bowl return even in stacks. */
public final class HuntingMealItem extends ConsumableItem {
    private final String note;
    private final List<MealBonus> bonuses;

    public HuntingMealItem(Properties properties, String note) {
        this(properties, note, List.of());
    }

    public HuntingMealItem(Properties properties, String note, List<MealBonus> bonuses) {
        super(properties, true);
        this.note = note;
        this.bonuses = List.copyOf(bonuses);
    }

    @Override
    public void affectConsumer(ItemStack stack, Level level, LivingEntity consumer) {
        if (DelightConfig.effectsEnabled()) for (MealBonus bonus : bonuses) consumer.addEffect(bonus.instance());
    }

    public List<MealBonus> bonuses() { return bonuses; }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flag) {
        super.appendHoverText(stack, context, lines, flag);
        if (!bonuses.isEmpty()) {
            lines.add(Component.translatable("tooltip.bossesrise_delight.battle_meal").withStyle(ChatFormatting.DARK_AQUA));
            for (MealBonus bonus : bonuses) {
                String description = bonus.effect().value().getDescriptionId();
                Component time = MobEffectUtil.formatDuration(bonus.instance(), 1.0F, context.tickRate());
                Component name = bonus.amplifier() > 0 ? Component.translatable("potion.withAmplifier", Component.translatable(description), Component.translatable("potion.potency." + bonus.amplifier())) : Component.translatable(description);
                lines.add(Component.translatable("tooltip.bossesrise_delight.bonus", name, time).withStyle(ChatFormatting.BLUE));
                lines.add(Component.translatable(description + ".description").withStyle(ChatFormatting.GRAY));
            }
        }
        if (note != null) lines.add(Component.translatable("tooltip.bossesrise_delight." + note).withStyle(ChatFormatting.GRAY));
    }
}
