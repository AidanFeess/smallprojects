## Script that holds all weapons and their data
## Server can tell clients to reference this data
## Obviously unsafe if we're worried about exploitation

import abc, time
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class WeaponType:
    name: str # e.g. melee or ranged
    description: str
    nocombo: List[str] # weapon types this weapon type can't combo with, e.g. melee and ranged

CommonWeaponTypes = {
    "Melee": WeaponType("Melee", "A very close range weapon like a sword.", {"Ranged"}),
    "Ranged": WeaponType("Ranged", "A long-range projectile based weapon.", {"Melee"}),
    "Explosive": WeaponType("Explosive", "An area-of-effect damage weapon.", {}),
    "Support": WeaponType("Support", "A supportive tool like healing.", {})
}

class Equippable(abc.ABC):
    """
    Abstract class that represents any equippable item like a weapon.
    """
    def __init__(self, name, icon):
        self.name = name
        self.icon = icon

    @abc.abstractmethod
    def equipped(self, player):
        return NotImplementedError
    
    @abc.abstractmethod
    def unequipped(self, player):
        return NotImplementedError
    
    @abc.abstractmethod
    def activated(self, player):
        return NotImplementedError

class Weapon(Equippable):
    def __init__(self, name, animation_prefix, sfx, anim_speed, icon, damage: float, damage_radius: int, range: int, projectile_speed: float, ammo: int, accuracy: int, weapon_types: List[WeaponType]):
        super().__init__(name, icon)
        self.damage = damage
        self.damage_radius = damage_radius
        self.range = range
        self.projectile_speed = projectile_speed
        self.ammo = ammo
        self.max_ammo = ammo
        self.accuracy = accuracy
        self.weapon_types = weapon_types
        self.animation_prefix = animation_prefix
        self.anim_speed = anim_speed
        self.sfx = sfx

        self.combo_count = 0  # Tracks how many times the player has attacked consecutively
        self.last_attack_time = 0  # Time of the last attack
        self.combo_timeout = 1.5  # Maximum time between attacks to maintain the combo (seconds)

    def equipped(self, player):
        player.current_weapon = self
    
    def unequipped(self, player):
        player.current_weapon = None

    def get_combo_animation(self):
        """Get the correct animation based on combo count."""
        combo_animation = f"{self.animation_prefix}_{self.combo_count + 1}"
        return combo_animation

    def reset_combo(self):
        """Reset the combo after a timeout or if the combo has ended."""
        self.combo_count = 0
        self.last_attack_time = 0

    def activate_combo(self):
        """Activate the combo logic for an attack."""
        current_time = time.time()
        if current_time - self.last_attack_time <= self.combo_timeout:
            self.combo_count += 1  # Progress the combo
        else:
            self.combo_count = 0  # Reset combo if too much time has passed

        self.last_attack_time = current_time

        # Check if there's a next combo animation (e.g., _2, _3), else reset to _1
        max_combo = 1  # This could be dynamic based on weapon
        if self.combo_count >= max_combo:
            self.combo_count = 0  # Reset to first combo

        return self.get_combo_animation()

    def activated(self, player):
        """Handle weapon activation (e.g., attack)."""
        animation_to_play = self.activate_combo()
        self.perform_attack(player)
        return animation_to_play

    @abc.abstractmethod
    def perform_attack(self, player):
        """Perform the attack, checking for enemies in range."""
        pass
    
    def apply_damage(self, enemies: Dict[str, Dict]) -> List[Dict[str, int]]:
        ret = []
        for id, _ in enemies.items():
            new = {}
            new[id] = self.damage
            ret.append(new)
        return ret
    
class Sword(Weapon):
    """
    A basic melee weapon.
    """
    def __init__(self, name, animation_prefix, sfx, anim_speed=1, icon=None, damage=25, damage_radius=0, range=150, projectile_speed=0, ammo=1, accuracy=100, weapon_types=[CommonWeaponTypes["Melee"]]):
        super().__init__(name, animation_prefix, sfx, anim_speed, icon, damage, damage_radius, range, projectile_speed, ammo, accuracy, weapon_types)

    def equipped(self, player):
        super().equipped(player)

    def unequipped(self, player):
        super().unequipped(player)

    def activated(self, player):
        self.ammo -= 1
        return super().activated(player)
    
    def perform_attack(self, player):
        pass

    def apply_damage(self, enemies):
        return super().apply_damage(enemies)

class Spear(Weapon):
    """
    A basic melee weapon.
    """
    def __init__(self, name, animation_prefix, sfx, anim_speed=1.5, icon=None, damage=15, damage_radius=0, range=175, projectile_speed=0, ammo=1, accuracy=100, weapon_types=[CommonWeaponTypes["Melee"]]):
        super().__init__(name, animation_prefix, sfx, anim_speed, icon, damage, damage_radius, range, projectile_speed, ammo, accuracy, weapon_types)

    def equipped(self, player):
        super().equipped(player)

    def unequipped(self, player):
        super().unequipped(player)

    def activated(self, player):
        self.ammo -= 1
        return super().activated(player)
    
    def perform_attack(self, player):
        pass

    def apply_damage(self, enemies):
        return super().apply_damage(enemies)