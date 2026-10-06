package com.suiyi.bossesrisedelight.verification;

import com.suiyi.bossesrisedelight.BossesRiseDelight;
import com.suiyi.bossesrisedelight.DelightItems;
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
import net.minecraftforge.event.TickEvent;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/** Uses the real inventory tooltip renderer and translated tooltip content. */
@EventBusSubscriber(modid = BossesRiseDelight.MOD_ID, value = Dist.CLIENT)
public final class KnifeTooltipReview {
    private static boolean started;
    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END) return;
        Minecraft client = Minecraft.getInstance();
        if (!started && Boolean.getBoolean("bossesrise_delight.knifeTooltipReview") && client.screen instanceof TitleScreen && client.getOverlay() == null) {
            started = true;
            client.options.guiScale().set(1);
            client.resizeDisplay();
            client.setScreen(new Review());
        }
    }
    private static final class Review extends Screen {
        private int frames, closeDelay;
        private volatile boolean captured;
        private String report = "";
        private Review() { super(Component.literal("Chef knife tooltips")); }
        @Override
        public void render(GuiGraphics gui, int mouseX, int mouseY, float partialTick) {
            gui.fill(0, 0, width, height, 0xFF263438);
            gui.drawString(font, Component.literal("Bosses'Rise Delight - knife tooltip review"), 26, 26, 0xE8DCC4, false);
            ItemStack[] knives = {DelightItems.DRAGONBONE_KNIFE.get().getDefaultInstance(), DelightItems.KRAKENTOOTH_KNIFE.get().getDefaultInstance()};
            for (int i = 0; i < knives.length; i++) {
                int x = 35 + i * 530;
                gui.drawString(font, knives[i].getHoverName(), x, 94, 0xE8DCC4, false);
                gui.pose().pushPose();
                gui.pose().translate(x, 138, 0);
                gui.pose().scale(4, 4, 1);
                gui.renderItem(knives[i], 0, 0);
                gui.pose().popPose();
                gui.renderTooltip(font, knives[i], x + 80, 150);
                if (frames == 0) {
                    List<Component> lines = Screen.getTooltipFromItem(minecraft, knives[i]);
                    String text = String.join("\n", lines.stream().map(Component::getString).toList());
                    if (!text.contains("狩猎加成") || !text.contains("+2") || !text.contains("主手") || !text.contains("不增加切菜产量")) {
                        throw new IllegalStateException("Knife tooltip is missing the visible hunting explanation: " + text);
                    }
                    report += knives[i].getHoverName().getString() + "\n" + text + "\n\n";
                }
            }
            gui.drawString(font, Component.literal("Existing reward explained; no changes to bonus amounts or knife combat behavior"), 26, height - 26, 0x9BB5A9, false);
            gui.flush();
            if (++frames == 30) Screenshot.grab(minecraft.gameDirectory, "knife-tooltips.png", minecraft.getMainRenderTarget(), message -> {
                try { Files.writeString(Path.of(minecraft.gameDirectory.getAbsolutePath(), "knife-tooltip-review.txt"), "Tooltip items checked: 2\n" + report); }
                catch (Exception error) { throw new RuntimeException(error); }
                captured = true;
            });
        }
        @Override public void tick() { if (captured && ++closeDelay > 20) minecraft.stop(); }
        @Override public boolean isPauseScreen() { return false; }
    }
}
