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
import pygame

GAME_NAME = "Iron Tide: 1944"

# Constants for screen size
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

# Constants for colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

COLORS = [WHITE, BLACK, RED, GREEN, BLUE]

## Directories
DIR_PLAYER_DATA = "./PlayerData"
DIR_SPRITES     = "./Sprites"
LOCALDIR = Path(__file__).parent  # Setting the local working directory to the parent of this file
SERVERDATADIR = LOCALDIR / "ServerData"
ABSSERVERDATADIR = SERVERDATADIR.resolve()

## Physics constants
FRICTION = 0.01  # Friction to apply on all entities
ANGULAR_FRICTION = 0.01 # same as friction but for angles
GRAVITY = 0.5   # Gravity constant

## Player data
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 50
MAX_ANGULAR_VELOCITY = 1

## Some dataclasses to make it clearer what is being sent between the client and server

# Client
@dataclass
class Position:
    x: int
    y: int

@dataclass
class GameData:
    HP: int

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

# Debug
@dataclass
class DebugKeyState:
    """Tracks the state and history of a key press"""
    is_pressed: bool
    press_time: float
    release_time: float
    hold_duration: float
    press_count: int

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