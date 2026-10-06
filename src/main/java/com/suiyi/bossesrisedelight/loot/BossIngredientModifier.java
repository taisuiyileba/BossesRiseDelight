package com.suiyi.bossesrisedelight.loot;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.suiyi.bossesrisedelight.DelightConfig;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.tags.TagKey;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.neoforged.neoforge.common.loot.IGlobalLootModifier;
import net.neoforged.neoforge.common.loot.LootModifier;

/** Adds ingredients without replacing or clearing the base mod's loot. */
public final class BossIngredientModifier extends LootModifier {
    public static final MapCodec<BossIngredientModifier> CODEC = RecordCodecBuilder.mapCodec(instance -> codecStart(instance)
            .and(instance.group(
                    BuiltInRegistries.ITEM.byNameCodec().fieldOf("ingredient").forGetter(m -> m.ingredient),
                    Codec.intRange(1, 64).fieldOf("minimum").forGetter(m -> m.minimum),
                    Codec.intRange(1, 64).fieldOf("maximum").forGetter(m -> m.maximum)))
            .apply(instance, BossIngredientModifier::new));
    private static final TagKey<Item> KNIVES = TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", "tools/knife"));
    private final Item ingredient;
    private final int minimum;
    private final int maximum;

    public BossIngredientModifier(LootItemCondition[] conditions, Item ingredient, int minimum, int maximum) {
        super(conditions);
        this.ingredient = ingredient;
        this.minimum = minimum;
        this.maximum = Math.max(minimum, maximum);
    }

    @Override
    protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> loot, LootContext context) {
        if (!DelightConfig.INGREDIENT_DROPS.get()) return loot;
        Player killer = context.getParamOrNull(LootContextParams.LAST_DAMAGE_PLAYER);
        int amount = (minimum + context.getRandom().nextInt(maximum - minimum + 1)) * DelightConfig.DROP_MULTIPLIER.get();
        if (killer != null && killer.getMainHandItem().is(KNIVES)) amount += DelightConfig.KNIFE_BONUS.get();
        while (amount > 0) {
            int stackSize = Math.min(amount, ingredient.getDefaultMaxStackSize());
            loot.add(new ItemStack(ingredient, stackSize));
            amount -= stackSize;
        }
        return loot;
    }

    @Override
    public MapCodec<? extends IGlobalLootModifier> codec() { return CODEC; }
}
