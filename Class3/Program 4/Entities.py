import pygame
import math
import os

from GameConstants import *

# Resize images to desired size
player_width, player_height = 150, 150

def SpriteLoader(sprite_name, sprite_directory, size):
    """Loads sprites for a given entity, including directional sprites and angle-specific sprites."""
    sprites = {}

    # Load the standard directional sprites
    sprites[0] = pygame.transform.scale(pygame.image.load(os.path.join(sprite_directory, sprite_name, "Right.png")).convert_alpha(), size)
    sprites[90] = pygame.transform.scale(pygame.image.load(os.path.join(sprite_directory, sprite_name, "Up.png")).convert_alpha(), size)
    sprites[180] = pygame.transform.scale(pygame.image.load(os.path.join(sprite_directory, sprite_name, "Left.png")).convert_alpha(), size)
    sprites[270] = pygame.transform.scale(pygame.image.load(os.path.join(sprite_directory, sprite_name, "Down.png")).convert_alpha(), size)

    # Load the angled sprites (Direction{number})
    angle_increment = 7.5
    # Right
    for i in range(1, 12):
        angle = i * angle_increment
        sprite_path = os.path.join(sprite_directory, sprite_name, f"Right{12-i}.png")
        if os.path.exists(sprite_path):
            sprites[angle] = pygame.transform.scale(pygame.image.load(sprite_path).convert_alpha(), size)
    # Left
    for i in range(1, 12):
        angle = 90 + i * angle_increment
        sprite_path = os.path.join(sprite_directory, sprite_name, f"Left{i}.png")
        if os.path.exists(sprite_path):
            sprites[angle] = pygame.transform.scale(pygame.image.load(sprite_path).convert_alpha(), size)
    # Bottom Right
    for i in range(1, 12):
        angle = 270 + i * angle_increment
        sprite_path = os.path.join(sprite_directory, sprite_name, f"DownRight{i}.png")
        if os.path.exists(sprite_path):
            sprites[angle] = pygame.transform.scale(pygame.image.load(sprite_path).convert_alpha(), size)
    # Bottom Left
    for i in range(1, 12):
        angle = 180 + i * angle_increment
        sprite_path = os.path.join(sprite_directory, sprite_name, f"DownLeft{12-i}.png")
        if os.path.exists(sprite_path):
            sprites[angle] = pygame.transform.scale(pygame.image.load(sprite_path).convert_alpha(), size)

    return sprites

class Entity:
    """Base entity class for all objects in the game (friendly, enemy, inanimate)"""
    def __init__(self, x, y, health, max_speed, sprite_name, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.health = health
        self.max_speed = max_speed
        self.size = (width, height)
        
        # Velocity and acceleration vectors
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        
        # Load sprites using the SpriteLoader utility
        self.sprites = SpriteLoader(sprite_name, DIR_SPRITES, self.size)
        
        # Default to "down" sprite at initialization
        self.current_sprite = self.sprites[270]

    def move(self):
        """Updates the entity's position based on velocity and acceleration"""
        # Update velocity with acceleration
        self.velocity += self.acceleration
        
        # Limit the velocity to the maximum speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        
        # Apply friction (from GameConstants)
        self.velocity *= (1 - FRICTION)
        
        # Move the entity using the velocity vector
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        
        # Only change the sprite if there is significant movement
        if self.velocity.length() > 0.1:
            # Get the angle of the velocity vector in degrees
            velocity_angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) % 360  # atan2 gives angle in radians; convert to degrees and normalize to [0, 360]
            
            # Find the closest angle to the velocity direction
            closest_angle = min(self.sprites.keys(), key=lambda angle: abs(angle - velocity_angle))
            
            # Set the sprite corresponding to the closest angle
            self.current_sprite = self.sprites[closest_angle]

    def apply_acceleration(self, accel_vector):
        """Applies an acceleration vector to the entity"""
        self.acceleration = accel_vector

    def stop(self):
        """Stops applying acceleration, allowing friction to slow down the entity"""
        self.acceleration = pygame.Vector2(0, 0)

    def draw(self, surface):
        """Draws the entity's sprite on the given surface"""
        surface.blit(self.current_sprite, self.rect)

    def take_damage(self, amount):
        """Reduces health when the entity takes damage"""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            return True  # Entity is dead
        return False

class Player(Entity):
    """Player class, inherits from Entity"""
    def __init__(self, x, y, health=100, max_speed=5, sprite_name="Player", width=150, height=150):
        super().__init__(x, y, health, max_speed, sprite_name, width, height)