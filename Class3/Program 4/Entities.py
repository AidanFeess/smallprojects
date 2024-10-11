import pygame
from Constants import *

class Entity:
    """Base entity class for all objects in the game (friendly, enemy, inanimate)"""
    def __init__(self, x, y, health, move_speed, sprite, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.health = health
        self.move_speed = move_speed
        self.sprite = pygame.transform.scale(sprite, (width, height))
        self.size = (width, height)

    def move(self, x_direction=0, y_direction=0):
        """Moves the entity in the specified direction"""
        self.rect.x += self.move_speed * x_direction
        self.rect.y += self.move_speed * y_direction

    def draw(self, surface):
        """Draws the entity's sprite on the given surface"""
        surface.blit(self.sprite, self.rect)

    def take_damage(self, amount):
        """Reduces health when the entity takes damage"""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            return True  # Entity is dead
        return False


class Player(Entity):
    """Player class, inherits from Entity"""
    def __init__(self, x, y, health=100, move_speed=5, sprite=None, width=50, height=50):
        if sprite is None:
            sprite = pygame.image.load(DIR_SPRITES + "/wizard.png").convert_alpha()
        super().__init__(x, y, health, move_speed, sprite, width, height)


class Spider(Entity):
    """Spider class, inherits from Entity"""
    def __init__(self, x, y, health=50, move_speed=4, sprite=None, width=40, height=40):
        if sprite is None:
            sprite = pygame.image.load(DIR_SPRITES + "/spider.png").convert_alpha()
        super().__init__(x, y, health, move_speed, sprite, width, height)

    def move(self):
        """Overrides move to move only right"""
        self.rect.x += self.move_speed
        if self.rect.right >= SCREEN_WIDTH:
            return True  # Spider reached the right side
        return False


class Projectile(Entity):
    """Projectile class, inherits from Entity"""
    def __init__(self, x, y, health=1, move_speed=7, sprite=None, width=5, height=10):
        if sprite is None:
            sprite = pygame.Surface((width, height))
            sprite.fill(WHITE)  # Basic white rectangle as projectile
        super().__init__(x, y, health, move_speed=move_speed, sprite=sprite, width=width, height=height)

    def move(self):
        """Moves the projectile upward"""
        self.rect.y -= self.move_speed
        if self.rect.bottom < 0:
            return True  # Projectile is off screen and should be removed
        return False