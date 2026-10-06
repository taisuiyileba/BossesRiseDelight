package com.suiyi.bossesrisedelight;

import com.mojang.serialization.MapCodec;
import com.suiyi.bossesrisedelight.loot.BossIngredientModifier;
import com.suiyi.bossesrisedelight.effect.CulinaryEffects;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.loot.IGlobalLootModifier;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

@Mod(BossesRiseDelight.MOD_ID)
public final class BossesRiseDelight {
    public static final String MOD_ID = "bossesrise_delight";
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MOD_ID);
    public static final DeferredRegister<MapCodec<? extends IGlobalLootModifier>> LOOT_MODIFIERS =
            DeferredRegister.create(NeoForgeRegistries.Keys.GLOBAL_LOOT_MODIFIER_SERIALIZERS, MOD_ID);

    static {
        LOOT_MODIFIERS.register("boss_ingredient", () -> BossIngredientModifier.CODEC);
        TABS.register("foods", () -> CreativeModeTab.builder()
                .title(Component.translatable("itemGroup.bossesrise_delight"))
                .icon(() -> DelightItems.DRAGON_CURRY.get().getDefaultInstance())
                .displayItems((parameters, output) -> DelightItems.ALL.forEach(item -> output.accept(item.get())))
                .build());
    }

    public BossesRiseDelight(IEventBus bus, ModContainer container) {
        DelightItems.ITEMS.register(bus);
        DelightBlocks.BLOCKS.register(bus);
        CulinaryEffects.EFFECTS.register(bus);
        TABS.register(bus);
        LOOT_MODIFIERS.register(bus);
        container.registerConfig(ModConfig.Type.SERVER, DelightConfig.SPEC);
    }

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }
}
