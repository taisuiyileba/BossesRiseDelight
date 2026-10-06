package com.suiyi.bossesrisedelight.verification;

import com.suiyi.bossesrisedelight.BossesRiseDelight;
import com.suiyi.bossesrisedelight.DelightItems;
import com.suiyi.bossesrisedelight.effect.CulinaryEffects;
import net.minecraft.client.renderer.texture.MissingTextureAtlasSprite;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.event.TickEvent;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** A separate automatic development client; never shipped or installed in the user's game. */
@EventBusSubscriber(modid = BossesRiseDelight.MOD_ID, value = Dist.CLIENT)
public final class ClientAssetReview {
    private static boolean started;

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        Minecraft client = Minecraft.getInstance();
        if (Boolean.getBoolean("bossesrise_delight.assetReview") && !started && client.screen instanceof TitleScreen && client.getOverlay() == null) {
            started = true;
            client.options.guiScale().set(1);
            client.resizeDisplay();
            client.setScreen(new ReviewScreen());
        }
    }

    private static final class ReviewScreen extends Screen {
        private int frames;
        private volatile boolean captured;
        private int closeDelay;
        private final List<String> missing = new ArrayList<>();
        private final List<String> missingEffects = new ArrayList<>();

        private ReviewScreen() { super(Component.literal("Bosses'Rise Delight - asset review")); }

        @Override
        public void render(GuiGraphics gui, int mouseX, int mouseY, float partialTick) {
            gui.fill(0, 0, width, height, 0xFF222C30);
            String version = ModList.get().getModContainerById(BossesRiseDelight.MOD_ID).orElseThrow().getModInfo().getVersion().toString();
            gui.drawString(font, "BOSSES'RISE DELIGHT " + version + "  |  Minecraft 1.20.1 / Forge", 28, 24, 0xEFE5CF, false);
            gui.drawString(font, "25 foods / 2 soul seasonings / 2 knives / 2 feasts / 13 original effects - actual Minecraft renderer", 28, 43, 0x9BB5A9, false);
            for (int i = 0; i < DelightItems.ALL.size(); i++) {
                ItemStack stack = DelightItems.ALL.get(i).get().getDefaultInstance();
                int x = 38 + (i % 6) * 174, y = 80 + (i / 6) * 108;
                var model = minecraft.getItemRenderer().getModel(stack, null, null, 0);
                if (frames == 0 && model == minecraft.getModelManager().getMissingModel()) missing.add(stack.getDescriptionId());
                gui.pose().pushPose();
                gui.pose().translate(x + 35, y, 0);
                gui.pose().scale(4, 4, 1);
                gui.renderItem(stack, 0, 0);
                gui.pose().popPose();
                gui.drawString(font, stack.getHoverName(), x, y + 68, 0xE8DCC4, false);
                gui.drawString(font, stack.getItem().getDescriptionId().replace("item.bossesrise_delight.", "").replace("block.bossesrise_delight.", ""), x, y + 82, 0x839D94, false);
            }
            int effectY = 80 + ((DelightItems.ALL.size() + 5) / 6) * 108;
            gui.drawString(font, "ORIGINAL CULINARY EFFECTS", 28, effectY, 0xEFE5CF, false);
            int index = 0;
            for (var effect : CulinaryEffects.EFFECTS.getEntries()) {
                var sprite = minecraft.getMobEffectTextures().get(effect.get());
                if (frames == 0 && sprite.contents().name().equals(MissingTextureAtlasSprite.getLocation())) missingEffects.add(effect.getId().toString());
                int x = 30 + (index % 7) * 152, y = effectY + 22 + (index / 7) * 62;
                gui.pose().pushPose();
                gui.pose().translate(x, y, 0);
                gui.pose().scale(2, 2, 1);
                gui.blit(0, 0, 0, 18, 18, sprite);
                gui.pose().popPose();
                gui.drawString(font, Component.translatable(effect.get().getDescriptionId()), x, y + 40, 0xE8DCC4, false);
                index++;
            }
            gui.drawString(font, "Native 16px sprites / binary alpha / original art / 4-serving feasts", 28, height - 24, 0x9BB5A9, false);
            gui.flush();
            frames++;
            if (frames == 30) {
                Screenshot.grab(minecraft.gameDirectory, "bossesrise-delight-in-game.png", minecraft.getMainRenderTarget(), message -> {
                    try {
                        Files.writeString(Path.of(minecraft.gameDirectory.getAbsolutePath(), "asset-review.txt"),
                                "Rendered items: " + DelightItems.ALL.size() + "\nMissing models: " + missing + "\nRendered effects: " + CulinaryEffects.EFFECTS.getEntries().size()
                                        + "\nMissing effects: " + missingEffects + "\nScreenshot: " + message.getString());
                    } catch (Exception e) { throw new RuntimeException(e); }
                    captured = true;
                });
            }
        }

        @Override
        public void tick() {
            if (captured && ++closeDelay > 20) minecraft.stop();
        }

        @Override
        public boolean isPauseScreen() { return false; }
    }
}
