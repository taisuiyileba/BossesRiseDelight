package com.suiyi.bossesrisedelight.effect;

import com.suiyi.bossesrisedelight.BossesRiseDelight;
import com.suiyi.bossesrisedelight.DelightConfig;
import java.util.function.Supplier;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.unusual.block_factorys_bosses.capability.entity.RollCap;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;

import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.Iterator;
import net.minecraft.world.level.Level;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;

/** Server-authoritative meal mechanics. Culinary damage never triggers another offensive proc. */
@EventBusSubscriber(modid = BossesRiseDelight.MOD_ID)
public final class MealCombatEvents {
    public static final ResourceKey<DamageType> CULINARY_DAMAGE = ResourceKey.create(Registries.DAMAGE_TYPE, BossesRiseDelight.id("culinary"));
    private static final Map<LivingEntity, State> STATES = new WeakHashMap<>();

    private static final class State {
        UUID emberTarget;
        int emberHits;
        long emberExpires, emberReady;
        float frostShield;
        boolean frostInitialized;
        long frostReady;
        long fireHealReady, reprisalReady, venomReady, tideReady, surgeReady, gillReady, resolveReady, resonanceReady;
        boolean wasSprinting, wasRolling, resolveHealPending;
        long surgeStrikeUntil, resolveStrikeUntil;
        int souls;
        boolean deathRewarded;
        WeakReference<LivingEntity> venomOwner = new WeakReference<>(null);
        final List<Echo> echoes = new ArrayList<>();
    }
    private record Echo(long due, float damage, WeakReference<LivingEntity> owner) {}
    private static State state(LivingEntity entity) { return STATES.computeIfAbsent(entity, key -> new State()); }
    private static long now(LivingEntity entity) { return entity.level().getGameTime(); }
    private static int tier(LivingEntity entity, Supplier<MobEffect> effect) {
        MobEffectInstance instance = entity.getEffect(effect.get());
        return instance == null ? 0 : 1 + Math.min(3, instance.getAmplifier());
    }
    private static boolean enabled(LivingEntity entity) { return !entity.level().isClientSide && DelightConfig.effectsEnabled(); }
    private static boolean culinary(DamageSource source) { return source.is(CULINARY_DAMAGE); }
    private static LivingEntity meleeAttacker(DamageSource source) {
        return !culinary(source) && source.getEntity() instanceof LivingEntity actor && source.getDirectEntity() == actor
                && !source.is(DamageTypeTags.IS_PROJECTILE) ? actor : null;
    }
    private static boolean friendly(LivingEntity actor, LivingEntity target) {
        return actor == target || actor.isAlliedTo(target)
                || target instanceof TamableAnimal pet && pet.isTame() && actor.getUUID().equals(pet.getOwnerUUID());
    }
    private static boolean mayProc(LivingEntity actor, LivingEntity target) {
        return !friendly(actor, target) && (!(target instanceof Player) || DelightConfig.pvpEnabled());
    }
    private static boolean hostile(LivingEntity actor, LivingEntity target) {
        return !friendly(actor, target) && (target instanceof Enemy || target instanceof Mob mob && mob.getTarget() == actor);
    }
    private static void damage(LivingEntity target, LivingEntity owner, float amount) {
        if (amount <= 0 || !target.isAlive() || !(target.level() instanceof ServerLevel level)) return;
        var type = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(CULINARY_DAMAGE);
        target.hurt(new DamageSource(type, null, owner), amount);
    }
    private static void particles(LivingEntity entity, net.minecraft.core.particles.SimpleParticleType type, int amount) {
        if (entity.level() instanceof ServerLevel level) level.sendParticles(type, entity.getX(), entity.getY() + entity.getBbHeight() * .55,
                entity.getZ(), amount, .35, .3, .35, .025);
    }
    private static void chill(LivingEntity actor, LivingEntity target) {
        if (mayProc(actor, target)) target.addEffect(new MobEffectInstance(CulinaryEffects.RIMEBOUND.get(), 80), actor);
    }
    private static void chillArea(LivingEntity actor) {
        for (LivingEntity target : actor.level().getEntitiesOfClass(LivingEntity.class, actor.getBoundingBox().inflate(3), e -> hostile(actor, e))) chill(actor, target);
        particles(actor, ParticleTypes.SNOWFLAKE, 12);
    }

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void beforeDamage(LivingHurtEvent event) {
        LivingEntity victim = event.getEntity();
        if (!enabled(victim) || event.getAmount() <= 0 || event.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) return;
        long time = now(victim);
        float amount = event.getAmount();
        LivingEntity attacker = meleeAttacker(event.getSource());
        if (attacker != null && mayProc(attacker, victim)) {
            State a = state(attacker);
            int surge = tier(attacker, CulinaryEffects.SAND_SURGE);
            if (surge > 0 && a.surgeStrikeUntil > time) {
                a.surgeStrikeUntil = 0;
                amount += 3F * surge * DelightConfig.damageScale();
                particles(victim, ParticleTypes.CRIT, 8);
            }
            int resolve = tier(attacker, CulinaryEffects.NETHER_RESOLVE);
            if (resolve > 0 && a.resolveStrikeUntil > time) {
                a.resolveStrikeUntil = 0;
                a.resolveHealPending = true;
                amount += 4F * resolve * DelightConfig.damageScale();
                particles(victim, ParticleTypes.SOUL, 10);
            }
        }
        event.setAmount(Math.max(0, amount));
    }

    /** Forge final damage is already reduced by armor and absorption. */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void defend(LivingDamageEvent event) {
        LivingEntity victim = event.getEntity();
        if (!enabled(victim) || event.getAmount() <= 0 || event.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) return;
        long time = now(victim);
        float amount = event.getAmount();
        State v = state(victim);
        int digest = tier(victim, CulinaryEffects.BLAZE_DIGEST);
        if (digest > 0 && event.getSource().is(DamageTypeTags.IS_FIRE)) amount *= .4F;
        int shell = tier(victim, CulinaryEffects.FROST_SHELL);
        if (shell > 0) {
            rechargeShell(victim, v, shell, time);
            if (v.frostShield > 0) {
                float used = Math.min(amount, v.frostShield);
                amount -= used;
                v.frostShield -= used;
                // Regeneration requires six seconds without damage, rather than a timer during constant hits.
                v.frostReady = time + 120;
                if (v.frostShield <= 0) chillArea(victim);
            } else v.frostReady = time + 120;
        }
        int gills = tier(victim, CulinaryEffects.ABYSS_GILLS);
        if (gills > 0 && victim.isInWater() && victim.getAirSupply() >= 80 && time >= v.gillReady && amount > 0) {
            float blocked = Math.min(4 + (gills - 1) * 2, amount * .35F);
            amount -= blocked;
            victim.setAirSupply(victim.getAirSupply() - 80);
            v.gillReady = time + 100;
            particles(victim, ParticleTypes.BUBBLE, 10);
        }
        // Forge has already consumed absorption before LivingDamageEvent.
        if (tier(victim, CulinaryEffects.SOUL_HARVEST) > 0 && v.souls >= 3
                && amount >= victim.getHealth()) {
            amount = Math.max(0, victim.getHealth() - 1);
            v.souls = 0;
            victim.removeEffect(CulinaryEffects.SOUL_HARVEST.get());
            particles(victim, ParticleTypes.SOUL_FIRE_FLAME, 24);
            if (victim instanceof ServerPlayer player) player.displayClientMessage(Component.translatable("message.bossesrise_delight.soul_saved"), true);
        }
        event.setAmount(Math.max(0, amount));
    }
    private static void rechargeShell(LivingEntity actor, State s, int tier, long time) {
        if (!s.frostInitialized || time >= s.frostReady && s.frostShield <= 0) {
            s.frostInitialized = true;
            s.frostShield = 4F + (tier - 1) * 2;
            s.frostReady = time + 120;
            particles(actor, ParticleTypes.SNOWFLAKE, 5);
        }
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void afterDamage(LivingDamageEvent event) {
        LivingEntity victim = event.getEntity();
        if (!enabled(victim) || event.getAmount() <= 0) return;
        long time = now(victim);
        State v = state(victim);
        float dealt = event.getAmount();
        float remainingHealth = victim.getHealth() - dealt;
        if (remainingHealth > 0 && tier(victim, CulinaryEffects.BLAZE_DIGEST) > 0 && event.getSource().is(DamageTypeTags.IS_FIRE) && time >= v.fireHealReady) {
            v.fireHealReady = time + 80;
            // This event runs before health subtraction; preserve healing even at full health.
            float healed = Math.min(1.5F, victim.getMaxHealth() - remainingHealth);
            event.setAmount(Math.max(0, dealt - healed));
            if (healed > dealt) victim.heal(healed - dealt);
            remainingHealth += healed;
            particles(victim, ParticleTypes.FLAME, 5);
        }
        if (tier(victim, CulinaryEffects.NETHER_RESOLVE) > 0 && remainingHealth > 0 && remainingHealth <= victim.getMaxHealth() * .4F && time >= v.resolveReady) {
            v.resolveStrikeUntil = time + 60;
            v.resolveReady = time + 160;
            particles(victim, ParticleTypes.SOUL_FIRE_FLAME, 8);
        }
        // Explicit recursion barrier: delayed strikes, poison ticks, rebounds and bursts cannot chain procs.
        if (culinary(event.getSource())) return;
        if (tier(victim, CulinaryEffects.FROST_REPRISAL) > 0 && time >= v.reprisalReady
                && event.getSource().getEntity() instanceof LivingEntity cause && cause.isAlive()
                && cause.distanceToSqr(victim) <= 64 && mayProc(victim, cause)) {
            v.reprisalReady = time + 80;
            chill(victim, cause);
            damage(cause, victim, 3 * tier(victim, CulinaryEffects.FROST_REPRISAL) * DelightConfig.damageScale());
            particles(cause, ParticleTypes.SNOWFLAKE, 10);
        }
        LivingEntity attacker = meleeAttacker(event.getSource());
        if (attacker == null || !mayProc(attacker, victim)) return;
        State a = state(attacker);
        if (a.resolveHealPending) { a.resolveHealPending = false; attacker.heal(2); }
        if (remainingHealth <= 0) return;
        int ember = tier(attacker, CulinaryEffects.EMBER_APPETITE);
        if (ember > 0) {
            if (time > a.emberExpires || !victim.getUUID().equals(a.emberTarget)) a.emberHits = 0;
            a.emberTarget = victim.getUUID();
            a.emberExpires = time + 160;
            if (++a.emberHits >= 3 && time >= a.emberReady) {
                a.emberHits = 0;
                a.emberReady = time + 40;
                particles(victim, ParticleTypes.FLAME, 16);
                damage(victim, attacker, 4 * ember * DelightConfig.damageScale());
                for (LivingEntity other : victim.level().getEntitiesOfClass(LivingEntity.class, victim.getBoundingBox().inflate(2), e -> e != victim && hostile(attacker, e))) {
                    damage(other, attacker, 2 * ember * DelightConfig.damageScale());
                }
            }
        }
        int venom = tier(attacker, CulinaryEffects.VENOM_SAC);
        if (venom > 0 && time >= a.venomReady && victim.isAlive()) {
            a.venomReady = time + 60;
            state(victim).venomOwner = new WeakReference<>(attacker);
            victim.addEffect(new MobEffectInstance(CulinaryEffects.CORROSIVE_VENOM.get(), 80, venom - 1), attacker);
            particles(victim, ParticleTypes.SPORE_BLOSSOM_AIR, 6);
        }
        int tide = tier(attacker, CulinaryEffects.TIDAL_ECHO);
        if (tide > 0 && time >= a.tideReady && victim.isAlive()) {
            a.tideReady = time + 60;
            State targetState = state(victim);
            if (targetState.echoes.size() < 32) targetState.echoes.add(new Echo(time + 12,
                    Math.min(5, Math.max(2, dealt * .3F)) * tide * DelightConfig.damageScale(), new WeakReference<>(attacker)));
        }
    }

    @SubscribeEvent
    public static void entityTick(LivingEvent.LivingTickEvent event) {
        updateEntity(event.getEntity());
    }
    public static void updateEntity(LivingEntity entity) {
        if (!enabled(entity) || !entity.isAlive()) return;
        State s = STATES.get(entity);
        boolean active = CulinaryEffects.BENEFICIAL.stream().anyMatch(effect -> entity.hasEffect(effect.get()));
        if (s == null && !active) return;
        if (s == null) s = state(entity);
        long time = now(entity);
        int shell = tier(entity, CulinaryEffects.FROST_SHELL);
        if (shell > 0) rechargeShell(entity, s, shell, time);
        else { s.frostInitialized = false; s.frostShield = 0; }
        int surge = tier(entity, CulinaryEffects.SAND_SURGE);
        boolean rolling = entity instanceof Player player && RollCap.fromPlayer(player).map(RollCap::isRolling).orElse(false);
        boolean sprintStart = entity.isSprinting() && !s.wasSprinting && entity.onGround();
        if (surge > 0 && (sprintStart || rolling && !s.wasRolling) && time >= s.surgeReady) {
            Vec3 direction = entity.getLookAngle().multiply(1, 0, 1);
            if (direction.lengthSqr() > .001) {
                if (!rolling) {
                    entity.setDeltaMovement(entity.getDeltaMovement().add(direction.normalize().scale(.7)));
                    entity.hasImpulse = true;
                    entity.hurtMarked = true;
                }
                s.surgeReady = time + 80;
                s.surgeStrikeUntil = time + 40;
                particles(entity, ParticleTypes.CLOUD, 8);
            }
        }
        s.wasSprinting = entity.isSprinting();
        s.wasRolling = rolling;
        if (tier(entity, CulinaryEffects.ABYSS_GILLS) > 0 && entity.isInWater() && time % 20 == 0) entity.setAirSupply(Math.min(entity.getMaxAirSupply(), entity.getAirSupply() + 30 * tier(entity, CulinaryEffects.ABYSS_GILLS)));
        if (!entity.hasEffect(CulinaryEffects.SOUL_HARVEST.get())) s.souls = 0;
        Iterator<Echo> echoes = s.echoes.iterator();
        while (echoes.hasNext()) {
            Echo echo = echoes.next();
            if (time < echo.due) continue;
            echoes.remove();
            LivingEntity owner = echo.owner.get();
            if (owner != null && owner.isAlive() && owner.level() == entity.level() && mayProc(owner, entity)) {
                damage(entity, owner, echo.damage);
                particles(entity, ParticleTypes.BUBBLE_POP, 12);
            }
        }
    }
    public static void corrosiveTick(LivingEntity target, int amplifier) {
        if (!enabled(target)) return;
        LivingEntity owner = state(target).venomOwner.get();
        if (owner != null && (!owner.isAlive() || owner.level() != target.level())) owner = null;
        if (target instanceof Player && !DelightConfig.pvpEnabled()) return;
        damage(target, owner, (1 + Math.min(3, amplifier) * .5F) * DelightConfig.damageScale());
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void death(LivingDeathEvent event) {
        LivingEntity target = event.getEntity();
        if (!enabled(target) || !(event.getSource().getEntity() instanceof LivingEntity killer) || !hostile(killer, target)) return;
        State t = state(target);
        if (t.deathRewarded) return;
        t.deathRewarded = true;
        State k = state(killer);
        if (tier(killer, CulinaryEffects.SOUL_HARVEST) > 0) {
            k.souls = Math.min(3, k.souls + 1);
            particles(killer, ParticleTypes.SOUL, 6);
            if (killer instanceof ServerPlayer player) player.displayClientMessage(Component.translatable("message.bossesrise_delight.war_souls", k.souls), true);
        }
        if (tier(killer, CulinaryEffects.HUNTER_RESONANCE) > 0 && now(killer) >= k.resonanceReady) {
            k.resonanceReady = now(killer) + 20;
            killer.heal(2);
            for (LivingEntity ally : killer.level().getEntitiesOfClass(LivingEntity.class, killer.getBoundingBox().inflate(6), e -> e != killer && e instanceof Player)) {
                if (killer.isAlliedTo(ally) || !DelightConfig.pvpEnabled()) { ally.heal(2); particles(ally, ParticleTypes.HAPPY_VILLAGER, 5); }
            }
            particles(killer, ParticleTypes.HAPPY_VILLAGER, 5);
        }
    }
    public static int warSouls(LivingEntity actor) { return state(actor).souls; }
    public static float frostShield(LivingEntity actor) { return state(actor).frostShield; }
    private MealCombatEvents() {}
}
