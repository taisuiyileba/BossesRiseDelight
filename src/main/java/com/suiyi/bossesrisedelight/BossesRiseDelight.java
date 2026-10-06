package com.suiyi.bossesrisedelight;

import com.mojang.serialization.Codec;
import com.suiyi.bossesrisedelight.loot.BossIngredientModifier;
import com.suiyi.bossesrisedelight.effect.CulinaryEffects;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.common.loot.IGlobalLootModifier;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;

@Mod(BossesRiseDelight.MOD_ID)
public final class BossesRiseDelight {
    public static final String MOD_ID = "bossesrise_delight";
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MOD_ID);
    public static final DeferredRegister<Codec<? extends IGlobalLootModifier>> LOOT_MODIFIERS =
            DeferredRegister.create(ForgeRegistries.Keys.GLOBAL_LOOT_MODIFIER_SERIALIZERS, MOD_ID);

    static {
        LOOT_MODIFIERS.register("boss_ingredient", () -> BossIngredientModifier.CODEC);
        TABS.register("foods", () -> CreativeModeTab.builder()
                .title(Component.translatable("itemGroup.bossesrise_delight"))
                .icon(() -> DelightItems.DRAGON_CURRY.get().getDefaultInstance())
                .displayItems((parameters, output) -> DelightItems.ALL.forEach(item -> output.accept(item.get())))
                .build());
    }

    public BossesRiseDelight() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        DelightItems.ITEMS.register(bus);
        DelightBlocks.BLOCKS.register(bus);
        CulinaryEffects.EFFECTS.register(bus);
        TABS.register(bus);
        LOOT_MODIFIERS.register(bus);
        ModLoadingContext.get().registerConfig(ModConfig.Type.SERVER, DelightConfig.SPEC);
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MOD_ID, path);
    }
}
