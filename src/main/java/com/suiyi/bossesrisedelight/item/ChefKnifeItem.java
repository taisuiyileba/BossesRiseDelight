package com.suiyi.bossesrisedelight.item;

import com.suiyi.bossesrisedelight.DelightConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TooltipFlag;
import vectorwing.farmersdelight.common.item.KnifeItem;
import java.util.List;

/** Keeps Farmer's Delight knife behavior and explains the existing hunting reward. */
public final class ChefKnifeItem extends KnifeItem {
    private final String profile;
    public ChefKnifeItem(Tier tier, Properties properties, String profile) {
        super(tier, properties);
        this.profile = profile;
    }
    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flag) {
        super.appendHoverText(stack, context, lines, flag);
        String prefix = "tooltip.bossesrise_delight.knife.";
        lines.add(Component.translatable(prefix + profile).withStyle(ChatFormatting.GRAY));
        boolean known = DelightConfig.SPEC.isLoaded();
        int bonus = known ? DelightConfig.KNIFE_BONUS.get() : 2;
        boolean enabled = !known || DelightConfig.INGREDIENT_DROPS.get();
        if (enabled && bonus > 0) {
            lines.add(Component.translatable(prefix + (known ? "hunting" : "hunting_default"), bonus).withStyle(ChatFormatting.GOLD));
        } else {
            lines.add(Component.translatable(prefix + "hunting_disabled").withStyle(ChatFormatting.DARK_GRAY));
        }
        lines.add(Component.translatable(prefix + "condition").withStyle(ChatFormatting.GRAY));
        lines.add(Component.translatable(prefix + "shared").withStyle(ChatFormatting.DARK_GRAY));
        lines.add(Component.translatable(prefix + "utility").withStyle(ChatFormatting.GRAY));
    }
}
