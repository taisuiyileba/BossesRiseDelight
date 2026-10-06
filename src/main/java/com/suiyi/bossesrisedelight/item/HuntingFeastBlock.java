package com.suiyi.bossesrisedelight.item;

import net.minecraft.core.BlockPos;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;
import vectorwing.farmersdelight.common.block.FeastBlock;

import java.util.function.Supplier;

/** Match interaction bounds to the platter and hotpot models at every serving stage. */
public final class HuntingFeastBlock extends FeastBlock {
    private final boolean hotpot;
    public HuntingFeastBlock(Properties properties, Supplier<Item> serving, boolean hotpot) {
        super(properties, serving, true);
        this.hotpot = hotpot;
    }

    @Override
    public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        if (hotpot) return Block.box(0, 0, 2, 16, 5, 14);
        return Block.box(2, 0, 2, 14, state.getValue(SERVINGS) == 0 ? 1 : 5, 14);
    }
}
