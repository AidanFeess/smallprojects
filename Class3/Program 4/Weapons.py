## Script that holds all weapons and their data
## Server can tell clients to reference this data
## Obviously unsafe if we're worried about exploitation

import pygame, abc
from dataclasses import dataclass
from typing import List
from Client import GameClient

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
    def __init__(self, name):
        self.name = name

    def equipped(self, player: GameClient):
        return NotImplementedError
    
    def unequipped(self, player: GameClient):
        return NotImplementedError
    
    def activated(self, player: GameClient):
        return NotImplementedError
    

class Weapon(Equippable):
    """
    An abstract base class for all weapons.
    """
    def __init__(self, name, damage: float, damage_radius: int, range: int, projectile_speed: float, ammo: int, accuracy: int, weapon_types: List[WeaponType]):
        super().__init__(name)

        self.damage = damage
        self.damage_radius = damage_radius
        self.range = range
        self.projectile_speed = projectile_speed
        self.ammo = ammo
        self.max_ammo = ammo
        self.accuracy = accuracy
        self.weapon_types = weapon_types # should probably check for valid types here

    def equipped(self, player: GameClient):
        return super().equipped()
    
    def unequipped(self, player: GameClient):
        return super().unequipped()
    
    def activated(self, player: GameClient):
        return super().activated()
    
class Sword(Weapon):
    """
    A basic melee weapon.
    """
    def __init__(self, name, damage=25, damage_radius=0, range=50, projectile_speed=0, ammo=1, accuracy=100, weapon_types=[CommonWeaponTypes["Melee"]]):
        super().__init__(name, damage, damage_radius, range, projectile_speed, ammo, accuracy, weapon_types)

    def equipped(self, player: GameClient):
        print(f"{player.username} equipped me!")

    def unequipped(self, player: GameClient):
        print(f"{player.username} unequipped me!")

    def activated(self, player: GameClient):
        print(f"{player.username} activated me!")