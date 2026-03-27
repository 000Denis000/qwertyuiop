# ============================================================
#  BACKYARD SURVIVAL v2  –  Status Effects
# ============================================================
from __future__ import annotations
from typing import Dict, List, Optional, Callable
from constants import *


class StatusEffect:
    """An active status effect on an entity."""

    def __init__(self, effect_id: str, duration: float,
                 tick_rate: float = 1.0, damage_per_tick: float = 0,
                 stat_mods: Dict[str, float] = None,
                 color=None, label: str = ""):
        self.effect_id       = effect_id
        self.duration        = duration
        self.time_remaining  = duration
        self.tick_rate       = tick_rate      # seconds between ticks
        self.damage_per_tick = damage_per_tick
        self.stat_mods       = stat_mods or {}
        self.color           = color or COL_PURPLE
        self.label           = label or effect_id
        self._tick_timer     = 0.0

    @property
    def expired(self) -> bool:
        return self.time_remaining <= 0

    def update(self, dt: float, owner) -> float:
        """Update timer, apply ticks. Returns damage done this frame."""
        self.time_remaining -= dt
        damage = 0.0
        if self.damage_per_tick > 0:
            self._tick_timer += dt
            while self._tick_timer >= self.tick_rate:
                self._tick_timer -= self.tick_rate
                damage += self.damage_per_tick
        return damage

    def refresh(self, duration: Optional[float] = None):
        self.time_remaining = duration if duration else self.duration


# ── Preset factory ──────────────────────────────────────────
_PRESETS = {
    SE_POISON: dict(
        damage_per_tick=4.0, tick_rate=1.5,
        stat_mods={},
        color=COL_POISON, label="Poison",
    ),
    SE_BURN: dict(
        damage_per_tick=6.0, tick_rate=1.0,
        stat_mods={},
        color=COL_FIRE, label="Burning",
    ),
    SE_BLEED: dict(
        damage_per_tick=3.0, tick_rate=0.8,
        stat_mods={},
        color=COL_RED, label="Bleeding",
    ),
    SE_STINK: dict(
        damage_per_tick=2.0, tick_rate=2.0,
        stat_mods={"defense": -10, "speed": -0.15},
        color=COL_STINKBUG, label="Stinked",
    ),
    SE_SLOW: dict(
        damage_per_tick=0, tick_rate=1.0,
        stat_mods={"speed": -0.35},
        color=COL_ICE, label="Slowed",
    ),
    SE_STUN: dict(
        damage_per_tick=0, tick_rate=1.0,
        stat_mods={"speed": -1.0, "attack_speed": -1.0},
        color=COL_YELLOW, label="Stunned",
    ),
    SE_REGEN: dict(
        damage_per_tick=-5.0, tick_rate=2.0,  # negative = heal
        stat_mods={},
        color=COL_LIME, label="Regenerating",
    ),
    SE_BOOST_ATK: dict(
        damage_per_tick=0, tick_rate=1.0,
        stat_mods={"damage": 0.25},
        color=COL_RED, label="Attack Up",
    ),
    SE_BOOST_DEF: dict(
        damage_per_tick=0, tick_rate=1.0,
        stat_mods={"defense": 10},
        color=COL_BLUE, label="Defense Up",
    ),
    SE_BOOST_SPD: dict(
        damage_per_tick=0, tick_rate=1.0,
        stat_mods={"speed": 0.30},
        color=COL_LIME, label="Speed Up",
    ),
}


def make_effect(effect_id: str, duration: float) -> StatusEffect:
    preset = _PRESETS.get(effect_id, {})
    return StatusEffect(
        effect_id        = effect_id,
        duration         = duration,
        tick_rate        = preset.get("tick_rate", 1.0),
        damage_per_tick  = preset.get("damage_per_tick", 0),
        stat_mods        = dict(preset.get("stat_mods", {})),
        color            = preset.get("color", COL_PURPLE),
        label            = preset.get("label", effect_id),
    )


class EffectManager:
    """Manages a collection of active status effects on one entity."""

    def __init__(self):
        self._effects: Dict[str, StatusEffect] = {}

    def apply(self, effect_id: str, duration: float):
        if effect_id in self._effects:
            self._effects[effect_id].refresh(duration)
        else:
            self._effects[effect_id] = make_effect(effect_id, duration)

    def remove(self, effect_id: str):
        self._effects.pop(effect_id, None)

    def has(self, effect_id: str) -> bool:
        return effect_id in self._effects

    def update(self, dt: float, owner) -> float:
        """Returns total damage dealt this frame."""
        total_dmg = 0.0
        expired = []
        for eid, eff in self._effects.items():
            dmg = eff.update(dt, owner)
            if dmg < 0:
                # Healing
                owner.health = min(owner.max_health, owner.health - dmg)
            else:
                total_dmg += dmg
            if eff.expired:
                expired.append(eid)
        for eid in expired:
            del self._effects[eid]
        return total_dmg

    def get_stat_mod(self, stat: str) -> float:
        """Get additive stat modifier from all active effects."""
        total = 0.0
        for eff in self._effects.values():
            total += eff.stat_mods.get(stat, 0.0)
        return total

    def active_list(self) -> List[StatusEffect]:
        return list(self._effects.values())

    def clear(self):
        self._effects.clear()

    def __len__(self):
        return len(self._effects)
