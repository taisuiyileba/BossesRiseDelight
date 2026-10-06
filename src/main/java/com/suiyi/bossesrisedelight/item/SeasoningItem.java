package com.suiyi.bossesrisedelight.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import java.util.List;

public final class SeasoningItem extends Item {
    private final String note;
    public SeasoningItem(Properties properties, String note) { super(properties); this.note = note; }
    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flag) {
        super.appendHoverText(stack, context, lines, flag);
        lines.add(Component.translatable("tooltip.bossesrise_delight." + note).withStyle(ChatFormatting.GRAY));
    }
}
