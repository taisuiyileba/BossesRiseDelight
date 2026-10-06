package com.suiyi.bossesrisedelight;

import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;
import vectorwing.farmersdelight.common.block.FeastBlock;
import com.suiyi.bossesrisedelight.item.HuntingFeastBlock;

public final class DelightBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(BossesRiseDelight.MOD_ID);
    public static final DeferredBlock<FeastBlock> HUNTERS_FEAST = BLOCKS.register("hunters_feast",
            () -> new HuntingFeastBlock(BlockBehaviour.Properties.of().strength(0.5F).sound(SoundType.WOOD).noOcclusion(),
                    () -> DelightItems.HUNTERS_FEAST_SERVING.get(), false));
    public static final DeferredBlock<FeastBlock> KRAKEN_HOTPOT = BLOCKS.register("kraken_hotpot",
            () -> new HuntingFeastBlock(BlockBehaviour.Properties.of().strength(0.5F).sound(SoundType.METAL).noOcclusion(),
                    () -> DelightItems.KRAKEN_HOTPOT_SERVING.get(), true));
    private DelightBlocks() {}
}
