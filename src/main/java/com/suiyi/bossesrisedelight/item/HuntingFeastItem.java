package com.suiyi.bossesrisedelight.item;

import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.Level;
import java.util.List;

public final class HuntingFeastItem extends BlockItem {
    public HuntingFeastItem(Block block, Properties properties) { super(block, properties); }
    @Override
    public void appendHoverText(ItemStack stack, Level level, List<Component> lines, TooltipFlag flag) {
        super.appendHoverText(stack, level, lines, flag);
        lines.add(Component.translatable("tooltip.bossesrise_delight." + BuiltInRegistries.BLOCK.getKey(getBlock()).getPath()).withStyle(ChatFormatting.GRAY));
    }
}
