#####################################################################
#   File containing constants that you might need in your assignment.
#   Make sure to import the library in all your files using a statement
#   like:
#   from Constants import *
#####################################################################

# NOTE: This is honestly more of a general data file at this point

# import libraries that you will need
from dataclasses import dataclass
from pathlib import Path
from typing import *
from PIL import Image
import pygame
import tkinter as tk # for getting screen size
from Weapons import *

GAME_NAME = "RETRO KNIGHTS"

# Constants for screen size
root = tk.Tk()
root.withdraw()
SCREEN_WIDTH = root.winfo_screenwidth()
SCREEN_HEIGHT = root.winfo_screenheight() - 60

# Constants for colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (135, 206, 235)
DARK_GREEN = (19, 109, 21)
DIRT_BROWN = (43, 24, 12)

DARK_GREY = (105, 105, 105)

COLORS = [WHITE, BLACK, RED, GREEN, BLUE]

## Directories
sprites_folder = Path(__file__).parent / 'Sprites'
LOCALDIR = Path(__file__).parent  # Setting the local working directory to the parent of this file
SERVERDATADIR = LOCALDIR / "ServerData"
ABSSERVERDATADIR = SERVERDATADIR.resolve()

## Physics constants
FRICTION = 0.01  # Friction to apply on all entities
GRAVITY = 400   # Gravity constant

## Player data
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40

## Enemy class

class Enemy:
    def __init__(self, position: pygame.Vector2, speed: float = 160.0, health: int = 100, scale: float = 1.5, size: int = 128, is_server=True):
        """
        Initializes the enemy with basic attributes.

        Args:
            position (pygame.Vector2): Starting position of the enemy.
            speed (float): Base horizontal movement speed of the enemy.
            health (int): Health of the enemy.
            scale (float): Scaling factor for rendering the enemy larger or smaller.
            size (int): Size of a single frame.
            is_server (bool): Whether this instance is running on the server (True) or client (False).
        """
        self.position = position
        self.velocity_x = 0  # Horizontal velocity
        self.velocity_y = 0  # Vertical velocity (affected by gravity)
        self.speed = speed
        self.health = health
        self.max_fall_speed = 20  # Maximum fall speed
        self.scale = scale
        self.target_position = None
        self.movement_direction = pygame.Vector2(0, 0)  # Direction of movement
        self.is_alive = True
        self.grounded = False  # To track whether the enemy is on the ground
        self.current_animation = "Idle"
        self.current_frame_index = 0
        self.frame_delay = 100  # Default milliseconds per frame
        self.is_server = is_server
        self.size = size  # Size of each frame in the sprite sheet
        self.max_frames = 0  # Number of frames in the current animation

        if not is_server:
            # Only load animations if running on the client
            self.last_frame_time = pygame.time.get_ticks()
            self.load_animation("Idle")
        else:
            # If on the server, determine the number of frames in the animation without loading them
            self.max_frames = self.determine_frame_count("Idle")

    def load_animation(self, action: str):
        """
        Loads the sprite sheet and creates animation frames. Only run on client side.
        """
        if self.is_server:
            return  # Do not load animations on the server

        sprite_sheet_path = f"{sprites_folder}/Enemies/{action}.png"
        sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        sheet_width, sheet_height = sprite_sheet.get_size()
        self.animation_frames = []  # Reset
        self.current_frame_index = 0
        self.max_frames = round(sheet_width // self.size)  # Calculate the number of frames from the sheet width

        # Split sprite sheet into frames
        for y in range(0, sheet_height, self.size):
            for x in range(0, sheet_width, self.size):
                frame = sprite_sheet.subsurface((x, y, self.size, self.size))
                self.animation_frames.append(frame)

    def update_frame_index(self):
        """
        Updates the frame index for animations. Should be handled both on the server and client.
        """
        if self.is_server:
            # Server increments the frame index based on time passed
            self.current_frame_index = (self.current_frame_index + 1) % self.max_frames
        else:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_frame_time > self.frame_delay:
                self.current_frame_index = (self.current_frame_index + 1) % self.max_frames
                self.last_frame_time = current_time

    def render(self, screen: pygame.Surface):
        """
        Renders the enemy on the screen with its current animation frame.

        Args:
            screen (pygame.Surface): The pygame screen to draw on.
        """
        if self.is_server or not self.animation_frames:
            return  # Prevent rendering if running on the server or no frames are loaded

        frame = self.animation_frames[self.current_frame_index]

        # Scale the frame based on the scale factor, but maintain the original resolution of the sprite.
        frame_width = int(self.size * self.scale)
        frame_height = int(self.size * self.scale)
        scaled_frame = pygame.transform.scale(frame, (frame_width, frame_height))

        # Blit the enemy at the current position (adjusted to center the sprite based on its scale)
        screen.blit(scaled_frame, (self.position.x - frame_width // 2, self.position.y - frame_height // 2))

    def apply_gravity(self, dt: float):
        """
        Applies gravity to the enemy's vertical velocity.

        Args:
            dt (float): Delta time for frame-independent movement.
        """
        if not self.grounded:
            self.velocity_y += GRAVITY * dt * 10  # Increase velocity downward due to gravity
            if self.velocity_y > self.max_fall_speed:
                self.velocity_y = self.max_fall_speed  # Cap the falling speed

    def move_towards_target(self, dt: float):
        """
        Moves the enemy towards the target position horizontally.

        Args:
            dt (float): Delta time for frame-independent movement.
        """
        if self.target_position is None:
            return

        # Calculate direction to the target
        direction = self.target_position - self.position
        if direction.length() > 0:
            direction = direction.normalize()

        # Apply horizontal movement speed (no impact on vertical movement here)
        self.velocity_x = direction.x * self.speed

    def chase_nearest_client(self, clients_positions: List[pygame.Vector2]):
        """
        Updates the target position to chase the nearest client.

        Args:
            clients_positions (List[pygame.Vector2]): List of all client positions.
        """
        if not clients_positions:
            return

        # Find the nearest client
        nearest_client = min(clients_positions, key=lambda pos: self.position.distance_to(pos))

        # Set target position to the nearest client's position
        self.target_position = nearest_client

        # Switch to the "Run" animation when chasing a client
        if self.current_animation != "Run":
            self.current_animation = "Run"
            if not self.is_server:
                self.load_animation("Run")

    def attack(self):
        """
        Triggers the enemy's attack behavior.
        """
        # Switch to the "Attack" animation when attacking
        if self.current_animation != "Attack":
            self.current_animation = "Attack"
            if not self.is_server:
                self.load_animation("Attack")

    def take_damage(self, damage: int):
        """
        Reduces the enemy's health when it takes damage.

        Args:
            damage (int): Amount of damage the enemy takes.
        """
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            self.die()
        else:
            self.load_animation("Hurt")

    def die(self):
        """
        Handles the enemy's death (e.g., removal from the game).
        """
        self.is_alive = False
        self.load_animation("Dead")

    def check_collision(self, terrain: List[List[Tuple[int, int]]]):
        """
        Checks for collisions with the terrain and updates the position accordingly.

        Args:
            terrain (List[List[Tuple[int, int]]]): List of building polygons representing the terrain.
        """
        for building in terrain:
            top_left = pygame.Vector2(building[0])
            bottom_right = pygame.Vector2(building[2])
            # Check if the enemy's X is within the building bounds and Y is above the ground level
            if top_left.x <= self.position.x <= bottom_right.x and self.position.y + (self.size * self.scale) // 2 >= top_left.y:
                self.grounded = True
                self.position.y = top_left.y - (self.size * self.scale) // 2
                self.velocity_y = 0  # Stop downward movement
                return
        self.grounded = False  # No collision, not grounded

    def determine_frame_count(self, action: str) -> int:
        """
        Uses PIL to determine the number of frames in the sprite sheet by checking the width of the image.

        Args:
            action (str): The name of the animation action (e.g., "Run", "Idle").
        
        Returns:
            int: The number of frames in the sprite sheet.
        """
        sprite_sheet_path = f"{sprites_folder}/Enemies/{action}.png"
        try:
            with Image.open(sprite_sheet_path) as img:
                sheet_width, _ = img.size  # Only care about the width
                return sheet_width // self.size  # Divide width by the frame size to get the number of frames
        except FileNotFoundError:
            print(f"Error: Could not find sprite sheet at {sprite_sheet_path}")
            return 1  # Default to 1 frame if the sprite sheet is not found

    def update(self, clients_positions: List[pygame.Vector2], terrain: List[List[Tuple[int, int]]], dt: float):
            """
            Updates the enemy's state, including movement, collisions, and chasing the nearest client.

            Args:
                clients_positions (List[pygame.Vector2]): List of all client positions.
                terrain (List[List[Tuple[int, int]]]): List of building polygons representing the terrain.
                dt (float): Delta time for frame-independent movement.
            """
            if not self.is_alive:
                return

            # Chase the nearest client and move towards them
            self.chase_nearest_client(clients_positions)
            self.move_towards_target(dt)

            # Apply gravity and update vertical movement
            self.apply_gravity(dt)

            # Update position based on velocities
            self.position.x += self.velocity_x * dt
            self.position.y += self.velocity_y * dt

            # Check for collisions with the terrain
            self.check_collision(terrain)

            # Update frame index for animations
            self.update_frame_index()

            # Check if the enemy should attack
            if self.target_position and self.position.distance_to(self.target_position) < 50:
                self.attack()
## Some dataclasses to make it clearer what is being sent between the client and server

# Client
@dataclass
class Position:
    x: int
    y: int

@dataclass
class GameData:
    HP: int 
    facing_right: bool
    current_animation: str
    current_frame_index: int
    last_frame_time: int
    player_scale: float
    velocity: float
    velocity_y: float
    grounded: bool
    movement_disabled: bool 
    current_weapon: Optional['Weapon'] 
    animation_in_progress: bool

@dataclass
class ClientPacket: 
    username: str
    position: Position
    gameData: GameData

# Server
@dataclass
class ServerJoinPacket:
    servername: str
    serverip: str
    serverport: int

@dataclass
class ServerPacket:
    terrain: List[int]
    clients_data: Dict[str, ClientPacket]
    enemy_data: Dict[str, Dict]  # A list of enemy data dictionaries for each enemy

# Objects
@dataclass
class ObjectType:
    isRect: bool
    isCircle: bool
    isSprite: bool

@dataclass
class WorldObject:
    worldPosition: Position
    color: pygame.color
    height: int
    width: int
    objectType: ObjectType
    sprite: pygame.sprite = None

# Helper functions
def ConvertBasicToWorldPosition(basic: pygame.Vector2) -> pygame.Vector2:
    
    '''
    Converts a basic pygame position to a world position, beginning from the center of the screen.
    '''
    return pygame.Vector2(SCREEN_WIDTH//2 - basic.x, SCREEN_HEIGHT//2 - basic.y)

def CalculateScreenPosition(worldPosition: pygame.Vector2, playerPosition: pygame.Vector2) -> pygame.Vector2:
    '''
    Converts a world position to screen coordinates relative to the player's position.
    This approach ensures all clients have a consistent frame of reference.
    '''
    return pygame.Vector2(
        SCREEN_WIDTH // 2 + (worldPosition.x - playerPosition.x),
        SCREEN_HEIGHT // 2 + (worldPosition.y - playerPosition.y)
    )

def lines_intersect(p1, p2, q1, q2):
    """Returns True if the line segments (p1, p2) and (q1, q2) intersect."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)


def line_rect_collision(line_start, line_end, rect):
    """Check if a line segment from line_start to line_end intersects with a rectangle."""
    # Check for collisions with each side of the rectangle (four edges)
    rect_lines = [
        (rect.topleft, rect.topright),
        (rect.topright, rect.bottomright),
        (rect.bottomright, rect.bottomleft),
        (rect.bottomleft, rect.topleft)
    ]

    for rect_line_start, rect_line_end in rect_lines:
        if lines_intersect(line_start, line_end, rect_line_start, rect_line_end):
            return True
    return False
