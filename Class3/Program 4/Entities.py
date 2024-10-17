import pygame
import math
import os

from GameConstants import *

def SpriteLoader(sprite_name, sprite_directory, size):
    """Loads sprites for a given entity, including directional sprites and angle-specific sprites."""
    sprites = {}
    sprites["Default"] = pygame.transform.scale(pygame.image.load(os.path.join(sprite_directory, sprite_name, "Up.png")).convert_alpha(), size)
    return sprites

class Entity:
    """Base entity class for all objects in the game (friendly, enemy, inanimate)"""
    def __init__(self, x, y, health, max_speed, sprite_name, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.health = health
        self.max_speed = max_speed
        self.size = (width, height)

        # Velocity and acceleration variables
        self.velocity = pygame.Vector2(0, 0)  # Linear velocity in 2D space
        self.acceleration = 0  # Linear acceleration, based on throttle control (W/S)

        # Angular variables (for ship's rotation)
        self.angle = 0  # Ship's current rotation in degrees (0 means facing up)
        self.angular_velocity = 0  # Speed of rotation (how fast it rotates)
        self.angular_acceleration = 0  # Change in angular velocity
        self.max_angular_velocity = 5  # Maximum angular velocity allowed

        # Load sprites using the SpriteLoader utility
        self.sprites = SpriteLoader(sprite_name, DIR_SPRITES, self.size)
        self.current_sprite = self.sprites["Default"]

    def move(self):
        """Updates the entity's position based on velocity and acceleration"""
        # Get the direction the ship is facing
        direction = pygame.Vector2(math.sin(math.radians(self.angle)), -math.cos(math.radians(self.angle)))

        # Calculate the target velocity based on the throttle (as a percentage of max speed)
        target_velocity = direction * (self.throttle * self.max_speed)

        # Calculate the difference between the current velocity and the target velocity
        velocity_difference = target_velocity - self.velocity

        # Apply acceleration based on the velocity difference (both accelerating and decelerating)
        if self.throttle != 0:
            if velocity_difference.length() > 0.1:  # If we're not at the target velocity
                # Normalize the velocity difference to get the direction, then apply acceleration
                acceleration_vector = velocity_difference.normalize() * self.acceleration
                
                # Apply the acceleration vector to the velocity
                self.velocity += acceleration_vector

                # Cap the velocity to avoid overshooting the target velocity
                if self.velocity.length() > target_velocity.length():
                    self.velocity = target_velocity  # Clamp to target velocity
        else:
            # If no throttle is applied, decelerate gradually
            self.velocity *= (1 - FRICTION)
            if self.velocity.length() < 0.01:
                self.velocity = pygame.Vector2(0, 0)  # Stop completely if velocity is very low

        # Apply friction to angular velocity as well
        self.angular_velocity *= (1 - ANGULAR_FRICTION)

        # Move the entity using the velocity vector
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        # Update the ship's angle based on angular velocity
        self.angle += self.angular_velocity

        # Keep the angle within the range of 0-360 degrees
        self.angle %= 360

        # Rotate the sprite based on the new angle
        self.current_sprite = pygame.transform.rotate(self.sprites["Default"], -self.angle)

        # Adjust the rect to ensure the rotated sprite is centered properly
        self.rect = self.current_sprite.get_rect(center=self.rect.center)

        
    def apply_throttle(self, throttle_input):
        """Sets the target throttle, which defines the target velocity as a percentage of max speed"""
        self.acceleration = throttle_input

    def apply_steering(self, angular_input):
        """Apply steering control (angular acceleration based on A/D input), dependent on current velocity"""
        # Only allow steering if the ship is moving above a certain speed
        speed_threshold = 0.1  # Define a speed below which turning is not allowed
        if self.velocity.length() > speed_threshold:
            # Scale the steering input by the current speed (faster movement allows faster turns)
            speed_factor = self.velocity.length() / self.max_speed  # Scale from 0 to 1
            # Reverse steering direction if moving backwards
            direction_factor = -1 if self.throttle < 0 else 1
            self.angular_acceleration = angular_input * speed_factor * direction_factor
            
            # Update maximum angular velocity based on current speed
            self.max_angular_velocity = MAX_ANGULAR_VELOCITY * speed_factor  # Decrease max angular velocity with speed
            self.angular_velocity = max(min(self.angular_velocity + self.angular_acceleration, self.max_angular_velocity), -self.max_angular_velocity)
        else:
            # If the ship is stationary or moving too slow, no steering
            self.angular_acceleration = 0
            self.angular_velocity = 0

    def stop(self):
        """Stops the ship, slowing it down due to friction"""
        self.acceleration = 0
        self.angular_acceleration = 0

    def update(self):
        """Updates both the acceleration and velocity (linear and angular)"""
        # Update angular velocity based on angular acceleration
        self.angular_velocity += self.angular_acceleration

        # Apply angular friction to reduce rotation gradually when not steering
        if self.angular_acceleration == 0:
            self.angular_velocity *= (1 - ANGULAR_FRICTION)
            if abs(self.angular_velocity) < 0.01:
                self.angular_velocity = 0

        # Update movement
        self.move()

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
    def __init__(self, x, y, health=100, max_speed=5, sprite_name="Player", width=PLAYER_WIDTH, height=PLAYER_HEIGHT):
        super().__init__(x, y, health, max_speed, sprite_name, width, height)
        self.throttle = 0  # Throttle ranges between -1 (full reverse) and 1 (full forward)

    def handle_input(self, keys):
        """Handles player input for throttle and steering"""
        throttle_step = 0.01  # Incremental throttle adjustment per tick
        steering_amount = 0.05  # How much angular velocity increases per tick

        # Check if Shift is being held
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            # If Shift + W or Shift + S is pressed, set throttle to 0 (emergency stop)
            if keys[pygame.K_w] or keys[pygame.K_s]:
                self.throttle = 0.0
        else:
            # Throttle control (W for forward, S for backward)
            if keys[pygame.K_w]:
                # Increase throttle gradually up to the max (1.0)
                self.throttle = min(1, self.throttle + throttle_step)
            elif keys[pygame.K_s]:
                # Decrease throttle gradually down to the minimum (-1.0 for reverse)
                self.throttle = max(-1, self.throttle - throttle_step)

        # Apply throttle as acceleration, so ship accelerates to the desired speed
        self.apply_throttle(self.throttle * self.max_speed)

        # Steering control (A for left, D for right)
        if keys[pygame.K_a]:
            self.apply_steering(-steering_amount)  # Rotate left
        elif keys[pygame.K_d]:
            self.apply_steering(steering_amount)   # Rotate right
        else:
            self.apply_steering(0)  # No steering input
