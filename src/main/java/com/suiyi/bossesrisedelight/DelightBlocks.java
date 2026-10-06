package com.suiyi.bossesrisedelight;

import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraft.world.level.block.Block;
import net.minecraftforge.registries.DeferredRegister;
import vectorwing.farmersdelight.common.block.FeastBlock;
import com.suiyi.bossesrisedelight.item.HuntingFeastBlock;

public final class DelightBlocks {
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(ForgeRegistries.BLOCKS, BossesRiseDelight.MOD_ID);
    public static final RegistryObject<FeastBlock> HUNTERS_FEAST = BLOCKS.register("hunters_feast",
            () -> new HuntingFeastBlock(BlockBehaviour.Properties.of().strength(0.5F).sound(SoundType.WOOD).noOcclusion(),
                    () -> DelightItems.HUNTERS_FEAST_SERVING.get(), false));
    public static final RegistryObject<FeastBlock> KRAKEN_HOTPOT = BLOCKS.register("kraken_hotpot",
            () -> new HuntingFeastBlock(BlockBehaviour.Properties.of().strength(0.5F).sound(SoundType.METAL).noOcclusion(),
                    () -> DelightItems.KRAKEN_HOTPOT_SERVING.get(), true));
    private DelightBlocks() {}
}
