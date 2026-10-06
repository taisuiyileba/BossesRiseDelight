package com.suiyi.bossesrisedelight.verification;

import com.mojang.blaze3d.platform.Lighting;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.suiyi.bossesrisedelight.BossesRiseDelight;
import com.suiyi.bossesrisedelight.DelightItems;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.model.BakedModelWrapper;
import org.joml.Vector3f;
import vectorwing.farmersdelight.common.registry.ModItems;
import java.nio.file.Files;
import java.nio.file.Path;

/** Development-only verification of the baked first/third-person item transforms. */
@EventBusSubscriber(modid = BossesRiseDelight.MOD_ID, value = Dist.CLIENT)
public final class KnifePoseReview {
    private static boolean started;
    @SubscribeEvent
    public static void tick(ClientTickEvent.Post event) {
        Minecraft mc = Minecraft.getInstance();
        if (!started && Boolean.getBoolean("bossesrise_delight.knifeReview") && mc.screen instanceof TitleScreen && mc.getOverlay() == null) {
            started = true;
            mc.options.guiScale().set(1);
            mc.resizeDisplay();
            mc.setScreen(new ReviewScreen());
        }
    }
    private static final class ReviewScreen extends Screen {
        private final ItemDisplayContext[] contexts = {ItemDisplayContext.FIRST_PERSON_RIGHT_HAND, ItemDisplayContext.FIRST_PERSON_LEFT_HAND,
                ItemDisplayContext.THIRD_PERSON_RIGHT_HAND, ItemDisplayContext.THIRD_PERSON_LEFT_HAND};
        private final String[] names = {"First person / right", "First person / left", "Third person / right", "Third person / left"};
        private int frames, closeDelay, checks;
        private volatile boolean captured;
        private ReviewScreen() { super(Component.literal("Knife held-model review")); }
        @Override
        public void render(GuiGraphics gui, int mouseX, int mouseY, float partialTick) {
            gui.fill(0, 0, width, height, 0xFF263438);
            gui.drawString(font, "HELD KNIFE MODELS - edge-facing correction", 28, 22, 0xEEDBC3, false);
            gui.drawString(font, "Minecraft baked item transforms; length/tip preserved, cutting edge turned outward", 28, 40, 0xAFBEAD, false);
            ItemStack reference = ModItems.IRON_KNIFE.get().getDefaultInstance();
            BakedModel vanilla = minecraft.getItemRenderer().getModel(reference, null, null, 0);
            ItemStack[] stacks = {reference, DelightItems.DRAGONBONE_KNIFE.get().getDefaultInstance(), DelightItems.DRAGONBONE_KNIFE.get().getDefaultInstance(),
                    DelightItems.KRAKENTOOTH_KNIFE.get().getDefaultInstance(), DelightItems.KRAKENTOOTH_KNIFE.get().getDefaultInstance()};
            String[] labels = {"Farmer's Delight reference", "Dragonbone - BEFORE", "Dragonbone - FIXED", "Krakentooth - BEFORE", "Krakentooth - FIXED"};
            for (int column = 0; column < 4; column++) {
                int x = 170 + column * 228;
                gui.drawString(font, names[column], x - 46, 72, 0xDCCBAB, false);
                boolean left = column == 1 || column == 3;
                for (int row = 0; row < 5; row++) {
                    int y = 115 + row * 155;
                    if (column == 0) gui.drawString(font, labels[row], 18, y + 38, row == 2 || row == 4 ? 0x9DC78E : 0xC8B9A7, false);
                    BakedModel model = minecraft.getItemRenderer().getModel(stacks[row], null, null, 0);
                    if (row == 1 || row == 3) {
                        model = new BakedModelWrapper<>(model) {
                            @Override
                            public BakedModel applyTransform(ItemDisplayContext context, PoseStack pose, boolean leftHand) {
                                vanilla.getTransforms().getTransform(context).apply(leftHand, pose);
                                return this;
                            }
                        };
                    }
                    if (frames == 0 && (row == 2 || row == 4)) {
                        verifyAxes(model, vanilla, contexts[column], left);
                        checks++;
                    }
                    gui.pose().pushPose();
                    gui.pose().translate(x + 52, y + 58, 150);
                    gui.pose().scale(115, -115, 115);
                    gui.pose().mulPose(Axis.YP.rotationDegrees(-35));
                    Lighting.setupFor3DItems();
                    minecraft.getItemRenderer().render(stacks[row], contexts[column], left, gui.pose(), gui.bufferSource(), 15728880, OverlayTexture.NO_OVERLAY, model);
                    gui.flush();
                    gui.pose().popPose();
                }
            }
            gui.drawString(font, "8 held contexts checked / existing inventory textures and gameplay retained", 28, height - 28, 0xAFBEAD, false);
            gui.flush();
            if (++frames == 30) Screenshot.grab(minecraft.gameDirectory, "knife-held-models.png", minecraft.getMainRenderTarget(), message -> {
                try { Files.writeString(Path.of(minecraft.gameDirectory.getAbsolutePath(), "knife-review.txt"), "Held contexts checked: " + checks + "\nTip axis preserved: true\nBlade edge reversed: true\n" + message.getString()); }
                catch (Exception ex) { throw new RuntimeException(ex); }
                captured = true;
            });
        }
        private void verifyAxes(BakedModel corrected, BakedModel original, ItemDisplayContext context, boolean left) {
            PoseStack oldPose = new PoseStack(), newPose = new PoseStack();
            original.getTransforms().getTransform(context).apply(left, oldPose);
            corrected.getTransforms().getTransform(context).apply(left, newPose);
            Vector3f oldTip = oldPose.last().pose().transformDirection(new Vector3f(1, 1, 0)).normalize();
            Vector3f newTip = newPose.last().pose().transformDirection(new Vector3f(1, 1, 0)).normalize();
            Vector3f oldEdge = oldPose.last().pose().transformDirection(new Vector3f(1, -1, 0)).normalize();
            Vector3f newEdge = newPose.last().pose().transformDirection(new Vector3f(1, -1, 0)).normalize();
            if (oldTip.dot(newTip) < .999F || oldEdge.dot(newEdge) > -.999F) throw new IllegalStateException("Incorrect held knife direction: " + context);
        }
        @Override public void tick() { if (captured && ++closeDelay > 20) minecraft.stop(); }
        @Override public boolean isPauseScreen() { return false; }
    }
}
