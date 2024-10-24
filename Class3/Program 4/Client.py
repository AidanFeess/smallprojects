import socket, struct
import threading, json, time, re, os
import pygame
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from collections import deque

from GameConstants import *
from Weapons import *

## Pygame setup
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags=pygame.FULLSCREEN)
current_scene = None
clock = pygame.time.Clock()
running = True
dt = 0

# Load sounds
sound_folder = Path(__file__).parent / 'Sound'
music_folder = sound_folder / 'Music'
sfx_folder = sound_folder / 'SFX'

# Menu GFX
sprites_folder = Path(__file__).parent / 'Sprites'

current_music = None

def SwitchMusic(newMusic, looped: bool):
    global current_music
    pygame.mixer.music.load(f"{music_folder}/{newMusic}")
    if looped:   
        pygame.mixer.music.play(loops=-1)
    else:
        pygame.mixer.music.play()
    current_music = newMusic

## Some global variables that need to be defined early
volume = 0
fullscreen = True

## Networking functions and classes
class NetworkClient:
    """
    A client class that handles client connections to the server.
    Stores and receives data from the server.
    Only meant to be used indirectly through GameClient.
    """

    def __init__(self, gameClient: 'GameClient', host: str = "127.0.0.1", port: int = 44200):
        # Basic server stuff
        self.host = host
        self.port = port
        self.gameClient = gameClient

        # For reconnection
        self.connection = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3

        # Connect to the server
        self.connect_to_server()

        # Start a separate thread for network communication
        self.network_thread = threading.Thread(target=self.run_network, daemon=True)
        self.network_thread.start()

    def run_network(self):
        """
        The main network loop runs in a separate thread, continuously sending
        and receiving data from the server.
        """
        while self.connected:
            try:
                # Send data to the server
                newPacket = self.serialize_client_data(
                    ClientPacket(
                        username=self.gameClient.username,
                        position=self.gameClient.position,
                        gameData=self.gameClient.gameData
                    )
                )
                self.send_with_length_prefix(newPacket)

                # Receive data from the server
                rawdata = self.connection.recv(10240)
                if not rawdata:
                    raise ConnectionError("Server closed")

                # Deserialize and update server data (including enemy data)
                self.gameClient.server_data = self.deserialize_server_data(rawdata)
                time.sleep(0.01)  # Send data every 10 ms

            except (socket.error, OSError, ConnectionError) as e:
                print(f"Network error: {e}")
                self.connected = False
                self.reconnect_to_server()

    def connect_to_server(self):
        """
        Attempts to establish a connection to the server.
        """
        try:
            self.connection = socket.create_connection((self.host, self.port))
            self.connected = True
            self.reconnect_attempts = 0

            # Receive the server info packet (initial handshake or entry message)
            serverData = self.connection.recv(1024)
            if "[CLOSECONNECTION]" in serverData.decode('utf-8'):
                self.connected = False
                return False
            self.serverInfo = self.deserialize_server_join_data(serverData)

        except (socket.error, OSError) as e:
            print(f"Failed to connect to server: {e}")
            self.connected = False
            self.reconnect_to_server()

    def reconnect_to_server(self):
        """
        Attempts to reconnect to the server.
        """
        while not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            print(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}...")
            try:
                time.sleep(2)  # Wait for 2 seconds before attempting to reconnect
                self.connect_to_server()
                if self.connected:
                    self.reconnect_attempts = 0  # Reset attempts on successful reconnection
                    return

            except Exception as e:
                print(f"Reconnect attempt failed: {e}")

        if not self.connected and self.reconnect_attempts >= self.max_reconnect_attempts:
            self.gameClient.message = ServerMessage("Failed to reconnect to the server.")

    def disconnect(self):
        """
        Gracefully closes the connection.
        """
        self.connected = False
        if self.connection:
            self.connection.close()
            print("Client disconnected.")

    def send_with_length_prefix(self, data: bytes):
        """
        Sends data with a length prefix.
        """
        try:
            length_prefix = struct.pack('!I', len(data))
            self.connection.sendall(length_prefix + data)
        except (socket.error, OSError) as e:
            print(f"Error sending data: {e}")
            self.reconnect_to_server()

    def serialize_client_data(self, packet: 'ClientPacket') -> bytes:
        """
        Converts the dataclass to a dictionary for JSON serialization.
        """
        # Serialize current_weapon separately if it exists
        weapon_data = None
        if packet.gameData.current_weapon:
            weapon_data = {
                "name": packet.gameData.current_weapon.name,
                "range": packet.gameData.current_weapon.range,
                "damage": packet.gameData.current_weapon.damage
            }

        data_dict = {
            "username": packet.username,
            "position": {"x": packet.position.x, "y": packet.position.y},
            "gameData": {
                "HP": packet.gameData.HP,
                "facing_right": packet.gameData.facing_right,
                "current_animation": packet.gameData.current_animation,
                "current_frame_index": packet.gameData.current_frame_index,
                "last_frame_time": packet.gameData.last_frame_time,
                "player_scale": packet.gameData.player_scale,
                "velocity": packet.gameData.velocity,
                "velocity_y": packet.gameData.velocity_y,
                "grounded": packet.gameData.grounded,
                "movement_disabled": packet.gameData.movement_disabled,
                "animation_in_progress": packet.gameData.animation_in_progress,
                "current_weapon": weapon_data
            }
        }

        return json.dumps(data_dict).encode('utf-8')

    def deserialize_server_join_data(self, data: bytes):
        """
        Deserializes the server info packet from the server.
        """
        data_dict = json.loads(data.decode('utf-8'))
        return ServerJoinPacket(
            servername=data_dict["servername"],
            serverip=data_dict["serverip"],
            serverport=data_dict["serverport"]
        )

    def deserialize_server_data(self, data: bytes) -> ServerPacket:
        """
        Deserializes the server packet from the server, including enemy data.
        """
        data_dict = json.loads(data.decode('utf-8'))

        clients_data = {}
        enemies = []

        # Ensure 'clients_data' is correctly deserialized into a dictionary
        if isinstance(data_dict['clients_data'], str):
            data_dict['clients_data'] = json.loads(data_dict['clients_data'])

        # Deserialize client data
        for client, client_data in data_dict['clients_data'].items():
            if client_data is None:
                continue

            client_data_dict = json.loads(client_data)
            weapon_data = client_data_dict['gameData'].get('current_weapon')
            current_weapon = None
            if weapon_data:
                current_weapon = Weapon(
                    name=weapon_data["name"],
                    range=weapon_data["range"],
                    damage=weapon_data["damage"]
                )

            position = Position(**client_data_dict['position'])
            gameData = GameData(
                HP=client_data_dict['gameData']['HP'],
                facing_right=client_data_dict['gameData']['facing_right'],
                current_animation=client_data_dict['gameData']['current_animation'],
                current_frame_index=client_data_dict['gameData']['current_frame_index'],
                last_frame_time=client_data_dict['gameData']['last_frame_time'],
                player_scale=client_data_dict['gameData']['player_scale'],
                velocity=client_data_dict['gameData']['velocity'],
                velocity_y=client_data_dict['gameData']['velocity_y'],
                grounded=client_data_dict['gameData']['grounded'],
                movement_disabled=client_data_dict['gameData']['movement_disabled'],
                animation_in_progress=client_data_dict['gameData']['animation_in_progress'],
                current_weapon=current_weapon
            )

            clients_data[client] = {
                "username": client_data_dict["username"],
                "position": position,
                "gameData": gameData
            }

        # Deserialize enemy data
        enemies = {}
        for id, enemy_info in data_dict['enemy_data'].items():
            enemies[id] = {
                "position": pygame.Vector2(enemy_info["position"]["x"], enemy_info["position"]["y"]),
                "health": enemy_info["health"],
                "animation_frame": enemy_info["animation_frame"],
                "current_animation": enemy_info["current_animation"],
                "is_alive": enemy_info["is_alive"]
            }

        # Return the deserialized server packet
        return ServerPacket(
            terrain=data_dict["terrain"],
            clients_data=clients_data,
            enemy_data=enemies  # Include enemy data
        )

def discover_servers_async(servers, lock, port=44200, timeout=3):
    """Function to discover servers asynchronously and update the servers list."""
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_sock.settimeout(timeout)

    broadcast_message = "DISCOVER_SERVERS".encode('utf-8')
    client_sock.sendto(broadcast_message, ('<broadcast>', port))

    start_time = pygame.time.get_ticks()

    try:
        while pygame.time.get_ticks() - start_time < timeout * 1000:
            try:
                response, serveraddress = client_sock.recvfrom(1024)
                with lock:
                    servers.append(response.decode('utf-8'))
            except socket.timeout:
                break
    except socket.error as e:
        print(f"Error discovering servers: {e}")
    client_sock.close()

def is_valid_ip(ip):
    """Function to check whether a given IP is an actual valid IP"""
    # Regular expression to match the IP format x.x.x.x where x is between 0 and 255
    ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    if re.match(ip_pattern, ip):
        # Ensure each part of the IP is between 0 and 255
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

## Game functions and classes
class GameClient():
    """
    A client class meant to be used directly for a player instance.

    Args:
        gameData (GameData): A dictionary of game data like health, upgrades, etc.
        username (str): The player's username
        position (Position): The player's current position

    In hindsight I should've separated this class's functions and an 'entity' class
    You live and you learn I guess...
    """
    def __init__(self, gameData: GameData, username: str = "Guest", position: Position = (0, 0)):
        self.gameData = gameData
        self.username = username
        self.position = position
        self.worldObjects = []
        self.server_data: ServerPacket = {}
        self.velocity = 5  # Horizontal movement speed
        self.velocity_y = 0  # Vertical velocity (gravity impact)
        self.grounded = False 
        self.movement_disabled = False
        self.networkClient = None
        self.facing_right = True
        self.current_animation = "Idle"   # Track the currently playing animation
        self.animation_in_progress = False  # To block other animations when sword swing is playing
        self.player_scale = 3
        self.just_equipped = False
        self.hit_objects = {}
        self.already_hit = []

        self.current_weapon: Weapon = None

        self.connInfo = {
            "ip": None, 
            "port": None
        }

        self.message: Optional[Message] = None  # Add message attribute for server messages like disconnects

        # Animation stuff
        self.animation_frames = []
        self.current_frame_index = 0
        self.frame_delay = 100  # milliseconds per frame
        self.current_animspeed = 1
        self.last_frame_time = pygame.time.get_ticks()
        self.animate("Idle")

        # Spawn the player above the center of the ground
        self.spawn(0, 400)

    def animate(self, sprite_sheet_path: str):
        """Load and set up animations."""
        sprite_sheet = pygame.image.load(f"{sprites_folder}/Player/{sprite_sheet_path}.png").convert_alpha()
        sheet_width, sheet_height = sprite_sheet.get_size()
        self.animation_frames = []

        # Split the sprite sheet into frames
        for y in range(0, sheet_height, 150):
            for x in range(0, sheet_width, 150):
                frame = sprite_sheet.subsurface((x, y, 150, 150))
                self.animation_frames.append(frame)

    def play_animation(self, screen, position):
        """
        Plays the animation with speed controlled by self.current_animspeed.

        Args:
            screen: The pygame screen object.
            position: The position to draw the animation.
        """
        current_time = pygame.time.get_ticks()

        # Adjust frame delay based on self.current_animspeed
        # Higher self.current_animspeed makes the animation faster, lower makes it slower
        adjusted_frame_delay = self.frame_delay / self.current_animspeed

        # Check if enough time has passed to change the frame
        if current_time - self.last_frame_time > adjusted_frame_delay:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
            self.last_frame_time = current_time

        try:
            # Get the current animation frame
            frame = self.animation_frames[self.current_frame_index]

            # Flip the frame horizontally if the player is facing left
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)

            # Scale the frame if needed
            if self.player_scale != 1:
                frame_width = int(frame.get_width() * self.player_scale)
                frame_height = int(frame.get_height() * self.player_scale)
                frame = pygame.transform.scale(frame, (frame_width, frame_height))

            # Blit the current frame to the screen
            screen.blit(frame, (position.x + (PLAYER_WIDTH * self.player_scale) // 2 - frame.get_width() // 2, position.y + (PLAYER_HEIGHT * self.player_scale) // 2 - frame.get_height() // 2))
        
        except Exception as e:
            print(f"Error rendering animation: {e}")
            pass

    def override_animation(self, animation_name: str, animspeed: int = 1):
        """Override any current animation with the given animation."""
        if self.animation_in_progress == True:
            return
        self.animation_in_progress = True
        self.current_animation = animation_name
        self.current_frame_index = 0
        self.last_frame_time = pygame.time.get_ticks()
        self.current_animspeed = animspeed
        self.animate(animation_name)

    def update_animation_state(self):
        """Checks if the current animation (sword swing or other) has finished."""
        if self.current_frame_index == len(self.animation_frames) - 1:
            # Animation is complete, allow other animations to play again
            self.animation_in_progress = False
            self.current_animspeed = 1
            self.current_animation = "Idle"  # Revert to idle after swing

    def connectToServer(self, ip: str = "127.0.0.1", port: int = 44200):
        """Creates a network client and attempts to connect to the given server"""
        self.connInfo["ip"], self.connInfo["port"] = ip, port
        self.message = None
        self.networkClient = NetworkClient(self, ip, port)

    def logout(self):
        """Resets the game state and disconnects from the server."""
        # Reset player position and movement
        self.position = pygame.Vector2(0, 0)
        self.velocity = 5  # Reset horizontal movement speed
        self.velocity_y = 0  # Reset vertical velocity (gravity impact)
        self.grounded = False  # The player is not grounded initially
        self.movement_disabled = False  # Reset to allow movement
        
        # Reset inventory, weapon, and animation states
        self.current_weapon = None  # Unequip any equipped weapon
        self.current_animation = "Idle"  # Reset to default idle animation
        self.current_frame_index = 0  # Reset animation frame index
        self.last_frame_time = pygame.time.get_ticks()  # Reset frame timing
        self.animation_in_progress = False  # No animation in progress
        self.current_animspeed = 1  # Reset animation speed to default

        # Reset world state
        self.worldObjects = []  # Clear any world objects
        self.server_data = None  # Clear server data
        self.message = None  # Clear any server messages

        # Reset connection info
        self.connInfo = {
            "ip": None,
            "port": None
        }

        # Reset networking state
        self.disconnectFromServer()

    def connectionInfo(self) -> tuple[str, int]:
        """Returns the GameClient's server connection info"""
        return (self.connInfo["ip"], self.connInfo["port"])

    def disconnectFromServer(self):
        if not self.networkClient:
            return
        self.networkClient.disconnect()
        self.networkClient.network_thread.join()

    def detect_collision(self):
        if not self.server_data or self.server_data == {}:
            return
        try:
            terrain = self.server_data.terrain
            player_x = self.position.x
            player_bottom_y = self.position.y + (PLAYER_HEIGHT * self.player_scale) // 2
            player_top_y = self.position.y - (PLAYER_HEIGHT * self.player_scale) // 2
            player_width = PLAYER_WIDTH * self.player_scale

            closest_building_top = None
            horizontal_collision = False
            player_new_x = self.position.x  # Store the player's new x position in case of horizontal collision

            # Loop through each building to check for collision
            for building in terrain:
                # Building is a list of four points: [top-left, top-right, bottom-right, bottom-left]
                top_left = pygame.Vector2(building[0])
                top_right = pygame.Vector2(building[1])
                bottom_left = pygame.Vector2(building[3])
                
                # Horizontal Collision Detection (blocking sides)
                if player_top_y <= top_left.y and player_bottom_y >= bottom_left.y:
                    # The player's top and bottom are within the vertical bounds of the building

                    if player_x + player_width > top_left.x and player_x < top_left.x:
                        # Player is hitting the left side of the building
                        player_new_x = top_left.x - player_width  # Prevent moving through the left side
                        horizontal_collision = True
                    elif player_x < top_right.x and player_x + player_width > top_right.x:
                        # Player is hitting the right side of the building
                        player_new_x = top_right.x  # Prevent moving through the right side
                        horizontal_collision = True

                # If the player is within the horizontal bounds of the building, check for grounding
                if top_left.x <= player_x <= top_right.x:
                    # The player is within the horizontal bounds of the building

                    # Top of the building is the Y value of the top-left point
                    building_top_y = top_left.y

                    # If this is the closest building top that the player can land on
                    if closest_building_top is None or building_top_y > closest_building_top:
                        closest_building_top = building_top_y

            # Update the player's position if there was horizontal collision
            if horizontal_collision:
                self.position.x = player_new_x

            # Now that we have the closest building top, check if the player is grounded on it
            if closest_building_top is not None and not horizontal_collision:
                buffer = 1  # Small buffer to avoid "floating"
                if player_bottom_y >= closest_building_top - buffer:
                    self.grounded = True
                    # Adjust the player's position so that the bottom of the player is at ground level
                    self.position.y = closest_building_top - (PLAYER_HEIGHT * self.player_scale) // 2
                else:
                    self.grounded = False
            else:
                self.grounded = False

            return self.grounded

        except Exception as e:
            print(f"Error detecting collision: {e}")
            return False

    def apply_gravity(self, dt):
        if not self.grounded:
            # Calculate the next position if gravity were applied
            next_velocity_y = self.velocity_y + GRAVITY * dt
            next_position_y = self.position.y + next_velocity_y * dt

            # Check if moving to this next position would cause a collision
            self.position.y = next_position_y
            if self.detect_collision():
                # If collision detected, adjust position to the ground level and reset velocity
                self.velocity_y = 0
                self.grounded = True
            else:
                # If no collision, update the velocity for the next frame
                self.velocity_y = next_velocity_y
        else:
            # If grounded, reset vertical velocity to 0 (with a small threshold to avoid jitter)
            if abs(self.velocity_y) < 0.5:
                self.velocity_y = 0
            self.grounded = True

    def handleMovement(self, keys):
        if self.movement_disabled or self.animation_in_progress:
            return

        moveVector = pygame.Vector2(0, 0)
        moving = False
        jumping = False
        falling = False

        # Horizontal movement
        if keys[pygame.K_a]:
            moveVector.x -= self.velocity
            self.facing_right = False  # Facing left
            moving = True
        if keys[pygame.K_d]:
            moveVector.x += self.velocity
            self.facing_right = True  # Facing right
            moving = True

        # Update the player's position with movement boundaries
        self.position.x = max(-2800, min(2800, self.position.x + moveVector.x))

        # Jumping logic
        if keys[pygame.K_SPACE] and self.grounded:
            jumping = True
            self.velocity_y = -65 * self.velocity  # Jumping sets a strong upward velocity
            self.grounded = False  # Player is no longer grounded when jumping

        # Falling logic: Detect when the player is falling
        if self.velocity_y > 0 and not self.grounded:
            falling = True

        # Animation handling
        if jumping:
            self.animate("Jump")
        elif falling:
            self.animate("Fall")
        elif moving and self.grounded:
            self.animate("Run")
        elif self.grounded:
            self.animate("Idle")    
        
    def get_slope_factor(self):
        """ Returns a factor between 0 (steep climb) and 1 (flat or downhill) """
        player_rect = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2, PLAYER_WIDTH, PLAYER_HEIGHT)
        terrain = self.server_data.terrain
        
        for i in range(len(terrain) - 1):
            line_start = pygame.Vector2(terrain[i])
            line_end = pygame.Vector2(terrain[i + 1])

            # Adjust these to screen coordinates for slope detection
            screen_line_start = CalculateScreenPosition(line_start, self.position)
            screen_line_end = CalculateScreenPosition(line_end, self.position)

            # Check if the player is colliding with the current terrain segment
            if line_rect_collision(screen_line_start, screen_line_end, player_rect):
                slope = (line_end.y - line_start.y) / (line_end.x - line_start.x + 0.01)  # Avoid division by zero
                if slope > 0:
                    return max(0.2, 1 - abs(slope))  # Smooth climbing by reducing gravity effect
                return 1  # Normal gravity on flat or downward terrain

        return 1  # Default gravity effect

    def draw(self, screen, debugger: 'Debugger'):
        # Define the player's central position for animation
        player_x = SCREEN_WIDTH // 2 - ((PLAYER_WIDTH * self.player_scale) // 2)
        player_y = SCREEN_HEIGHT // 2 - ((PLAYER_HEIGHT * self.player_scale) // 2)

        # Create the hitbox rectangle
        hitbox_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH * self.player_scale, PLAYER_HEIGHT * self.player_scale)

        # Delegate hitbox drawing to the debugger
        if debugger.show_debug:
            debugger.draw_hitbox(screen, hitbox_rect, self.username)

        # Adjust the position for the animation to center it on the hitbox
        animation_x = player_x
        animation_y = player_y 

        # Draw the player’s animation at the adjusted position
        self.play_animation(screen, pygame.Vector2(animation_x, animation_y))

    def drawWorldObjects(self, screen):
        for obj in self.worldObjects:
            screenPosition = CalculateScreenPosition(obj.worldPosition, self.position)
            if obj.objectType.isSprite and obj.sprite:
                screen.blit(obj.sprite.image, (screenPosition.x, screenPosition.y))
            elif obj.objectType.isCircle:
                pygame.draw.circle(screen, obj.color, (screenPosition.x, screenPosition.y), obj.width)
            elif obj.objectType.isRect:
                pygame.draw.rect(screen, obj.color, (screenPosition.x - obj.width // 2, screenPosition.y - obj.height // 2, obj.width, obj.height))

    def drawTerrain(self, screen):
        if not self.server_data or self.server_data == {}:
            return
        try:
            # Get the terrain (list of buildings, each building is a list of four points)
            buildings = self.server_data.terrain

            for building in buildings:
                # Adjust each point in the building to the player's screen position
                adjusted_points = [CalculateScreenPosition(pygame.Vector2(x, y), self.position) for x, y in building]

                # Draw each building as a separate polygon
                pygame.draw.polygon(screen, DARK_GREY, adjusted_points)

        except Exception as e:
            print(f"Error drawing terrain: {e}")

    def drawOtherClients(self, screen):
        if not self.server_data:
            return
        
        clients_data = self.server_data.clients_data  # clients_data is already a dict

        for client_key, client in clients_data.items():
            if client_key == self.networkClient.host: # ignore yourself
                continue
            client_data = clients_data[client_key]
            if client_data is None:
                continue

            # Assuming client_data['gameData'] is a GameData object
            game_data = client['gameData']

            # Extract client-specific data
            client_position: Position = client['position']
            client_facing_right = game_data.facing_right
            client_username = client['username']
            client_current_animation = game_data.current_animation
            client_current_frame_index = game_data.current_frame_index
            client_last_frame_time = game_data.last_frame_time
            client_player_scale = game_data.player_scale

            # Convert client world position to screen position
            screen_position = CalculateScreenPosition(pygame.Vector2(client_position.x, client_position.y), self.position)

            # Load the client's animation frames based on their current animation state
            sprite_sheet_path = f"{sprites_folder}/Player/{client_current_animation}.png"
            sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
            sheet_width, sheet_height = sprite_sheet.get_size()
            client_animation_frames = []

            # Split the sprite sheet into frames
            for y in range(0, sheet_height, 150):
                for x in range(0, sheet_width, 150):
                    frame = sprite_sheet.subsurface((x, y, 150, 150))
                    client_animation_frames.append(frame)

            # Calculate the frame delay (using the default frame delay for the player, you can adjust this if needed)
            frame_delay = self.frame_delay

            # Adjust frame timing based on the client's last frame time
            current_time = pygame.time.get_ticks()
            if current_time - client_last_frame_time > frame_delay:
                client_current_frame_index = (client_current_frame_index + 1) % len(client_animation_frames)
                client_last_frame_time = current_time
            
            # Get the current frame of the client's animation
            try:
                frame = client_animation_frames[client_current_frame_index]

                # Flip the frame horizontally if the client is facing left
                if not client_facing_right:
                    frame = pygame.transform.flip(frame, True, False)

                # Scale the frame to the client's scale factor
                if client_player_scale != 1:
                    frame_width = int(frame.get_width() * client_player_scale)
                    frame_height = int(frame.get_height() * client_player_scale)
                    frame = pygame.transform.scale(frame, (frame_width, frame_height))

                # Blit the current frame to the screen at the adjusted position
                screen.blit(frame, (screen_position.x + (PLAYER_WIDTH * client_player_scale) // 2 - frame.get_width() // 2, 
                                    screen_position.y + (PLAYER_HEIGHT * client_player_scale) // 2 - frame.get_height() // 2))
            except Exception as e:
                print(f"Error rendering client animation: {e}")

            # Render the username above the client
            font = pygame.font.SysFont(None, 40)
            text = font.render(client_username, True, BLACK)
            text_rect = text.get_rect(center=(screen_position.x + PLAYER_WIDTH // 2, screen_position.y - 20))
            screen.blit(text, text_rect)

    def spawn(self, spawn_x: int = 0, spawn_height: int = 100):
        """
        Spawns the player at a given location, where 0,0 is the center of the world.
        """
        self.position = pygame.Vector2(spawn_x, -spawn_height) 
        self.velocity_y = 0
        self.grounded = False

    def activate_weapon(self):
        """Activates the currently equipped weapon, if any."""
        if self.current_weapon and not self.animation_in_progress:
            global volume
            anim = self.current_weapon.activated(self)
            self.override_animation(anim, animspeed=self.current_weapon.anim_speed)
            pygame.mixer.Sound(f"{sound_folder}\\SFX\\{self.current_weapon.sfx}.mp3").play().set_volume(volume)
            
            # Create the weapon hitbox and store it for rendering during animation
            self.weapon_hitbox = self._create_weapon_hitbox()
            self.animation_in_progress = True  # The animation has started
            
            # Reset hit objects for the new attack
            self.hit_objects = {}

    def _create_weapon_hitbox(self):
        """Creates a hitbox based on the player's current weapon and position, adjusting for screen offset."""
        weapon_range = self.current_weapon.range
        if self.facing_right:
            # Create the hitbox in front of the player
            hitbox_position = pygame.Vector2(
                self.position.x + (PLAYER_WIDTH // 2),  # In front of the player
                self.position.y - (PLAYER_HEIGHT // 2)  # Vertically centered on the player
            )
        else:
            # Create the hitbox to the left of the player
            hitbox_position = pygame.Vector2(
                self.position.x - (PLAYER_WIDTH // 2) - weapon_range,  # Behind the player
                self.position.y - (PLAYER_HEIGHT // 2)  # Vertically centered on the player
            )
        screen_position = CalculateScreenPosition(hitbox_position, self.position)
        hitbox = pygame.Rect(
            screen_position.x,  # Hitbox x position
            screen_position.y,  # Hitbox y position
            weapon_range,       # Hitbox width (weapon range)
            PLAYER_HEIGHT       # Hitbox height (player height)
        )

        return hitbox

    def _check_hitbox_intersections(self, hitbox):
        """Checks for intersections between the weapon hitbox, world objects, and enemies."""
        hit_objects = {}

        # Check intersections with enemies
        for id, enemy in self.server_data.enemy_data.items():
            if id in self.already_hit:
                continue
            else:
                self.already_hit.append(id)
            # Retrieve the enemy's position and size directly from the server data
            enemy_screen_pos = CalculateScreenPosition(pygame.Vector2(enemy['position'].x, enemy['position'].y), self.position)
            enemy_size = enemy.get('size', 128)  # Default to 128 if no size is provided by server data
            
            # Adjust the enemy hitbox creation based on actual enemy size
            enemy_hitbox = pygame.Rect(
                enemy_screen_pos.x - (enemy_size // 2),
                enemy_screen_pos.y - (enemy_size // 2),
                enemy_size,
                enemy_size
            )
            
            # Draw the enemy hitbox for debugging
            debugger.draw_weapon_hitbox(screen, enemy_hitbox)
            
            # Check if the enemy's hitbox collides with the weapon's hitbox
            if hitbox.colliderect(enemy_hitbox):
                hit_objects[id] = enemy

        return hit_objects

    def update(self, screen, dt):
        self.apply_gravity(dt)
        self.detect_collision()
        self.handleMovement(pygame.key.get_pressed())

        if self.position.y > SCREEN_HEIGHT:  # If the player falls too far
            self.spawn(100)

        if self.animation_in_progress:
            self.weapon_hitbox = self._create_weapon_hitbox()
            self.hit_objects = self._check_hitbox_intersections(self.weapon_hitbox)
            # deal_to = self.current_weapon.apply_damage(self.hit_objects)
            debugger.draw_weapon_hitbox(screen, self.weapon_hitbox)
        else:
            self.weapon_hitbox = None  # Clear hitbox when animation ends

        self.update_animation_state()  # Check if current animation has finished
        self.drawTerrain(screen)
        self.drawWorldObjects(screen)
        self.draw(screen, debugger)
        self.drawOtherClients(screen)

class Message(ABC):
    """
    Abstract base class for various in-game messages.
    """
    def __init__(self, message_text: str):
        self.message_text = message_text

    @abstractmethod
    def display(self, screen):
        pass

class ServerMessage(Message):
    """
    Represents a message when the server closes or reconnection fails.
    """
    def __init__(self, message_text: str = "Server Closed!"):
        super().__init__(message_text)

    def display(self, screen):
        font = pygame.font.SysFont(None, 60)
        text = font.render(self.message_text, True, (255, 0, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.fill((0, 0, 0))  # Black background for the message
        screen.blit(text, text_rect)

        # Draw confirm button
        button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
        pygame.draw.rect(screen, (0, 0, 0), button_rect)
        pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)
        button_text = font.render("Confirm", True, (255, 255, 255))
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)

        # Event handling for the confirm button
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                # Return to main menu and disconnect
                global current_scene
                current_scene = MainMenu(screen)
                newClient.disconnectFromServer()
                return

newClientBaseData = GameData(
    HP=100,
    facing_right=True,
    current_animation="Idle",
    current_frame_index=0,
    last_frame_time=0,
    player_scale=3,
    velocity=0,
    velocity_y=0,
    grounded=False,
    movement_disabled=False,
    current_weapon=None,
    animation_in_progress=False
)
newClient = GameClient(newClientBaseData, "User1", pygame.Vector2(0, 0))

## Debug
class Debugger:
    def __init__(self, max_fps_samples: int = 60):
        # Initialize debug state
        self.show_debug = True
        self.font_size = 24
        self.font = pygame.font.Font(None, self.font_size)
        self.text_color = (128, 128, 128)
        
        # FPS tracking
        self.fps_samples = deque(maxlen=max_fps_samples)
        self.last_time = time.time()
        
        # Performance metrics
        self.frame_times = deque(maxlen=60)
        self.last_frame_time = time.time()
        
        # Network metrics
        self.last_ping: Optional[str] = None
        self.ping_interval = 2.0
        self.last_ping_time = 0

    def draw_hitbox(self, screen, player_rect, username):
        """Draw the hitbox and username if hitbox display is enabled"""
        
        # Draw the hollow rectangle for the player's hitbox
        pygame.draw.rect(screen, BLUE, player_rect, 2)

        # Render the player's name above the hitbox
        font = pygame.font.SysFont(None, 40)
        text = font.render(username, True, BLACK)
        text_rect = text.get_rect(center=(player_rect.centerx, player_rect.y - 20))
        screen.blit(text, text_rect)

    def ping_server(self, hostname: str, port: int) -> str:
        """Ping server and return latency in milliseconds"""
        try:
            if not hostname or not port:
                return None
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)

            start_time = time.time()
            s.connect((hostname, port))
            s.close()

            ping_ms = (time.time() - start_time) * 1000
            self.last_ping = str(round(ping_ms))
            return self.last_ping
        except socket.error as e:
            print(f"Failed to ping {hostname}:{port}, Error: {e}")
            return None
    
    def update_ping(self, hostname: str, port: int) -> None:
        """Update ping if enough time has passed"""
        current_time = time.time()
        if current_time - self.last_ping_time >= self.ping_interval:
            self.ping_server(hostname, port)
            self.last_ping_time = current_time
    
    def display_debug_info(self, screen: pygame.Surface, server_info: Tuple[str, int], newClient: GameClient) -> None:
        """Display debug overlay with various metrics and connected clients"""
        if not self.show_debug:
            return
        
        # Update ping
        self.update_ping(server_info[0], server_info[1])
        
        # Calculate metrics
        current_fps = self.update_fps()
        
        # Left side - General debug info
        debug_lines = [
            f"FPS: {current_fps:.1f}",
            f"Ping: {self.last_ping}ms" if self.last_ping else "Ping: N/A",
            f"Server: {server_info[0]}:{server_info[1]}",
        ]
        
        # Draw left side debug information
        y_offset = 10
        for line in debug_lines:
            text_surface = self.font.render(line, True, self.text_color)
            screen.blit(text_surface, (10, y_offset))
            y_offset += self.font_size
        
        # Right side - Connected clients
        x_offset = screen.get_width() - 300
        y_offset = 10
        
        # Header
        client_header = self.font.render("Connected Clients:", True, self.text_color)
        screen.blit(client_header, (x_offset, y_offset))
        y_offset += self.font_size * 1.5
        
        # Display connected clients from newClient.allClients
        server_data = newClient.server_data  # clients_data is already a dict

        if not server_data:
            return
        for client_key, client in server_data.clients_data.items():
            if client is None:
                return
            if client_key == newClient.networkClient.host: # ignore yourself
                continue
            
            username = client["username"]
            
            # Display client info
            client_lines = [
                f"User: {username}",
                f"IP: {client_key}",
                "---"
            ]
            
            for line in client_lines:
                text_surface = self.font.render(line, True, self.text_color)
                screen.blit(text_surface, (x_offset, y_offset))
                y_offset += self.font_size
            
            # Add spacing between clients
            y_offset += self.font_size // 2
                
    def update_fps(self) -> float:
        """Update and return current FPS"""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        if dt > 0:
            fps = 1.0 / dt
            self.fps_samples.append(fps)
        
        return sum(self.fps_samples) / len(self.fps_samples) if self.fps_samples else 0
    
    def toggle_debug(self) -> None:
        """Toggle debug overlay visibility"""
        self.show_debug = not self.show_debug
    
    def draw_weapon_hitbox(self, screen, hitbox):
        """Draw the weapon's hitbox for debugging purposes."""
        if self.show_debug and hitbox:
            # Draw the hitbox as a red rectangle
            pygame.draw.rect(screen, (255, 0, 0), hitbox, 2)  # Red color, border width 2

debugger = Debugger()

### Pygame Functions

## Menus

class Menu(ABC):
    """
    Abstract class for rendering in-game menus
    """
    def __init__(self, title: str, options: list, font_size: int = 40):
        self.title = title
        self.options = options
        self.font_size = font_size
        self.active_option = None
        self.option_rects = []

    @abc.abstractmethod
    def on_select(self, selected_option: int):
        return NotImplementedError

    def handle_mouse_input(self, mouse_pos, mouse_click):
        for idx, option_rect in enumerate(self.option_rects):
            if option_rect.collidepoint(mouse_pos):
                self.active_option = idx
                if mouse_click[0]:
                    self.on_select(idx)

    def render(self, screen):
        font = pygame.font.SysFont(None, self.font_size)

        title_surf = font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 100))
        screen.blit(title_surf, title_rect)

        self.option_rects = []
        for idx, option in enumerate(self.options):
            option_color = (255, 0, 0) if idx == self.active_option else (255, 255, 255)
            option_surf = font.render(option, True, option_color)
            option_rect = option_surf.get_rect(center=(screen.get_width() // 2, 200 + idx * 50))
            self.option_rects.append(option_rect)
            screen.blit(option_surf, option_rect)

class InventoryMenu(Menu):
    def __init__(self, client, cell_size: int = 64, padding: int = 10):
        inventory_items = [  # (Item, Amount) tuples
            [(Sword("Iron Sword", "SwordAttack", "SwordSwing"), 1)],
            [],
            [(Spear("Spear", "SpearAttack", "SpearThrust"), 3)],
            [(Sword("Great Sword", "GreatswordAttack", "SwordSwingBeefy", anim_speed=.75, damage=45, range=200), 3)],
            [],
        ]

        # Ensure each row has the correct number of columns (filling with empty slots)
        for row in inventory_items:
            while len(row) < 5:
                row.append((None, 0))

        super().__init__(title="Inventory", options=inventory_items)
        self.columns = 5
        self.rows = 5
        self.cell_size = cell_size
        self.padding = padding
        self.position = (0, 0)
        self.client = client
        self.visible = False
        self.arrow_rect = pygame.Rect(0, 0, 50, 50)
        self.icon_cache = {}
        self.option_rects = []

    def add_item(self, item, amount: int):
        """Adds an item to the inventory, or increases its amount if it already exists."""
        # Check if the item is already in the inventory
        for row in self.options:
            for i, (existing_item, existing_amount) in enumerate(row):
                if existing_item == item:
                    # If the item already exists, increase the amount
                    row[i] = (existing_item, existing_amount + amount)
                    return

        # If the item is not found, add it to the first available empty slot
        for row in self.options:
            for i, (existing_item, existing_amount) in enumerate(row):
                if existing_item is None:
                    row[i] = (item, amount)
                    return

    def remove_item(self, item, amount: int):
        """Removes an amount of an item from the inventory. If the amount reaches zero, the item remains but with 0 quantity."""
        for row in self.options:
            for i, (existing_item, existing_amount) in enumerate(row):
                if existing_item == item:
                    # Decrease the amount and set it to 0, but don't remove the item
                    new_amount = max(0, existing_amount - amount)
                    row[i] = (existing_item, new_amount)
                    return

    def load_icon(self, item):
        """Loads the icon for an item and caches it for future use."""
        if item.icon not in self.icon_cache:
            icon_surface = pygame.image.load(f"{sprites_folder}/Items/{item.icon}").convert_alpha()
            icon_surface = pygame.transform.scale(icon_surface, (self.cell_size - 10, self.cell_size - 10))  # Scale the icon to fit the cell
            self.icon_cache[item.icon] = icon_surface
        return self.icon_cache[item.icon]

    def set_position(self, screen):
        """Sets the position of the inventory and arrow button on the screen."""
        # Set the position of the inventory based on the screen size
        self.position = (
            screen.get_width() - (self.columns * (self.cell_size + self.padding)) - 20,
            screen.get_height() - (self.rows * (self.cell_size + self.padding)) - 20
        )

        # Set the position of the arrow just to the left of the inventory
        self.arrow_rect.x = self.position[0] - 60  # Place the arrow 60 pixels to the left of the inventory
        self.arrow_rect.y = self.position[1] - 10  # Align the arrow with the top of the inventory

    def on_select(self, row_idx: int, col_idx: int):
        """Handles selection of an inventory item for equipping without using it."""
        selected_item, amount = self.options[row_idx][col_idx]
        
        # Check if an item is selected and has quantity
        if selected_item and amount > 0:
            if self.client.current_weapon:
                if self.client.current_weapon == selected_item:
                    return
                self.client.current_weapon.unequipped(self.client)
            self.remove_item(selected_item, 1)
            selected_item.equipped(self.client)
            self.client.just_equipped = True  # Track that an item was just equipped

    def toggle_inventory(self):
        """Toggles the visibility of the inventory."""
        self.visible = not self.visible

    def render(self, screen):
        # Always render the toggle arrow button, regardless of inventory visibility
        self.set_position(screen)
        self._draw_toggle_arrow(screen)

        # If inventory is not visible, return here after drawing the arrow
        if not self.visible:
            return

        # Render the inventory when it's visible
        self.set_position(screen)
        self._draw_inventory_background(screen)

        # Clear previous option rectangles (click detection areas)
        self.option_rects.clear()

        # Iterate through the inventory items and render them
        for row_idx, row in enumerate(self.options):
            for col_idx, (option, amount) in enumerate(row):
                if option is not None:
                    self._render_item_cell(screen, row_idx, col_idx, option, amount)

    def _draw_toggle_arrow(self, screen):
        """Draws the arrow that toggles the inventory."""
        pygame.draw.rect(screen, (255, 255, 255), self.arrow_rect)
        arrow = ">" if not self.visible else "<"
        arrow_font = pygame.font.SysFont(None, 50)
        arrow_surf = arrow_font.render(arrow, True, (0, 0, 0))
        screen.blit(arrow_surf, (self.arrow_rect.x + 15, self.arrow_rect.y + 5))

    def _draw_inventory_background(self, screen):
        """Draws the semi-transparent background for the inventory."""
        background_width = self.columns * (self.cell_size + self.padding) + 20
        background_height = self.rows * (self.cell_size + self.padding) + 20
        background = pygame.Surface((background_width, background_height), pygame.SRCALPHA)
        background.fill((0, 0, 0, 128))
        screen.blit(background, (self.position[0] - 10, self.position[1] - 10))

    def _render_item_cell(self, screen, row_idx, col_idx, option, amount):
        """Renders a single cell in the inventory grid."""
        x = self.position[0] + col_idx * (self.cell_size + self.padding)
        y = self.position[1] + row_idx * (self.cell_size + self.padding)

        # Draw the cell rectangle
        cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

        # Only draw the border and content if there is an item
        if option:
            self._draw_cell_border(screen, cell_rect, option)

            # Draw item icon, name, and amount
            self._draw_item_icon(screen, cell_rect, option)
            self._draw_item_name(screen, cell_rect, option)
            self._draw_item_amount(screen, cell_rect, amount)

        # Store the cell position for click detection regardless of content
        self.option_rects.append((cell_rect, row_idx, col_idx))

    def _draw_cell_border(self, screen, cell_rect, option):
        """Draws the border of the inventory cell if the item is present."""
        if option == self.client.current_weapon:
            pygame.draw.rect(screen, (255, 215, 0), cell_rect, 4)  # Golden border for equipped weapon
        else:
            pygame.draw.rect(screen, (255, 255, 255), cell_rect, 2)  # Regular border

    def _draw_item_icon(self, screen, cell_rect, option):
        """Draws the icon for the item in the inventory."""
        # Cache icon and avoid reloading/resizing each frame
        if option and option.icon:
            icon_surface = self.icon_cache.get(option.icon)
            if not icon_surface:
                # Load and scale the icon only once, cache it
                icon_surface = pygame.image.load(f"{sprites_folder}/Items/{option.icon}").convert_alpha()
                icon_surface = pygame.transform.scale(icon_surface, (self.cell_size - 10, self.cell_size - 10))
                self.icon_cache[option.icon] = icon_surface
            icon_rect = icon_surface.get_rect(center=cell_rect.center)
            screen.blit(icon_surface, icon_rect)

    def _draw_item_name(self, screen, cell_rect, option):
        """Draws the name of the item in the inventory."""
        if option and option.name:
            option_font = pygame.font.SysFont(None, 30)
            option_surf = option_font.render(option.name, True, (255, 255, 255))
            option_rect = option_surf.get_rect(center=cell_rect.center)
            screen.blit(option_surf, option_rect)

    def _draw_item_amount(self, screen, cell_rect, amount):
        """Draws the amount of the item in the inventory."""
        if amount > 0:
            amount_font = pygame.font.SysFont(None, 24)
            amount_surf = amount_font.render(str(amount), True, (255, 255, 255))
            amount_rect = amount_surf.get_rect(topright=(cell_rect.right - 5, cell_rect.top + 5))
            screen.blit(amount_surf, amount_rect)

    def handle_mouse_input(self, mouse_pos, mouse_click):
        """Handles mouse input for toggling the inventory and selecting items."""
        # Check if the arrow button was clicked
        if self.arrow_rect.collidepoint(mouse_pos) and mouse_click == 1:
            self.toggle_inventory()

        if self.visible:
            # Check if an inventory item was clicked
            for cell_rect, row_idx, col_idx in self.option_rects:
                if cell_rect.collidepoint(mouse_pos) and mouse_click == 1:
                    self.on_select(row_idx, col_idx)

class PauseMenu(Menu):
    def __init__(self, options: list):
        super().__init__(title="Pause Menu", options=options, font_size=40)
        self.title_font_size = 70  # Larger font size for the title
        self.position = (0, 0)

    def set_position(self, screen):
        self.position = (screen.get_width() // 2, screen.get_height() // 2)

    def on_select(self, selected_option: int):
        if self.options[selected_option] == "Resume":
            return "resume"
        elif self.options[selected_option] == "Options":
            return "options"
        elif self.options[selected_option] == "Log Out":
            return "logout"

    def render(self, screen):
        global volume
        if volume > 10: # reduce volume in pause screen
            volume = 10
        self.set_position(screen)

        # Create a transparent overlay
        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(128)
        overlay.fill((50, 50, 50))
        screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont(None, self.title_font_size)
        option_font = pygame.font.SysFont(None, self.font_size)

        # Render the title
        title_surf = title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(self.position[0], self.position[1] - 200))
        screen.blit(title_surf, title_rect)

        # Don't interact with the title when clicked
        if title_rect.collidepoint(pygame.mouse.get_pos()):
            return

        self.option_rects = []
        for idx, option in enumerate(self.options):
            # Highlight the option on mouse hover
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = False

            option_rect = pygame.Rect(self.position[0] - 150, self.position[1] + idx * 80, 300, 60)
            if option_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, DARK_GREEN, option_rect, border_radius=5)
                is_hovered = True
            else:
                pygame.draw.rect(screen, (255, 255, 255), option_rect, 2, border_radius=5)

            option_surf = option_font.render(option, True, (255, 255, 255) if not is_hovered else (0, 0, 0))
            option_surf_rect = option_surf.get_rect(center=option_rect.center)
            screen.blit(option_surf, option_surf_rect)

            self.option_rects.append(option_rect)

    def handle_mouse_input(self, mouse_pos, mouse_click):
        for idx, option_rect in enumerate(self.option_rects):
            if option_rect.collidepoint(mouse_pos):
                if mouse_click[0]:  # Left click
                    return self.on_select(idx)
        return None

class OptionMenu(Menu):
    def __init__(self):
        super().__init__(title="", options=[])

    def render(self, screen):
        global volume
        global fullscreen
        
        self.set_position(screen)

        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(128)
        overlay.fill((50, 50, 50))
        screen.blit(overlay, (0, 0))

        font = pygame.font.SysFont(None, 40)

        volume_text = font.render(f"Volume: {volume}", True, (255, 255, 255))
        screen.blit(volume_text, (self.position[0] - 100, self.position[1] - 150))

        slider_rect = pygame.Rect(self.position[0] - 100, self.position[1] - 100, 200, 10)
        pygame.draw.rect(screen, (255, 255, 255), slider_rect)

        volume_pos = int(slider_rect.x + (volume / 100) * slider_rect.width)
        pygame.draw.circle(screen, (255, 0, 0), (volume_pos, slider_rect.y + 5), 8)

        toggle_text = "Fullscreen: On" if fullscreen else "Fullscreen: Off"
        toggle_surf = font.render(toggle_text, True, (255, 255, 255))
        toggle_rect = toggle_surf.get_rect(center=(self.position[0], self.position[1]))
        pygame.draw.rect(screen, (255, 255, 255), toggle_rect.inflate(20, 10), 2)
        screen.blit(toggle_surf, toggle_rect)

        self.slider_rect = slider_rect
        self.toggle_rect = toggle_rect

    def handle_mouse_input(self, mouse_pos, mouse_click, mouse_held):
        global volume
        global fullscreen

        if self.slider_rect.collidepoint(mouse_pos) and (mouse_click[0] or mouse_held[0]):
            relative_x = mouse_pos[0] - self.slider_rect.x
            volume = max(0, min(100, int((relative_x / self.slider_rect.width) * 100)))

        if self.toggle_rect.collidepoint(mouse_pos) and mouse_click[0]:
            fullscreen = not fullscreen
            pygame.display.toggle_fullscreen()

    def on_select(self, selected_option: int):
        pass

    def set_position(self, screen):
        self.position = (screen.get_width() // 2, screen.get_height() // 2)

## Scenes
class Scene(ABC):
    """
    Abstract class that represents a game scene like a menu
    or combat scene
    """
    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()

    @abstractmethod
    def handle_click(self, position):
        """
        Handle click events, this method must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def render(self):
        """
        Render the scene, this method must be implemented by subclasses.
        """
        pass  

    def update(self):
        self.render()
        pygame.display.flip()

class Gameplay(Scene):
    def __init__(self, screen):
        super().__init__(screen)
        self.paused = False
        self.in_options_menu = False
        self.inventoryMenu = InventoryMenu(newClient)
        self.pauseMenu = PauseMenu(["Resume", "Options", "Log Out"])
        self.optionMenu = OptionMenu()

        # Scale factor for reducing the size of images (e.g., 0.5 to make the images smaller)
        self.scale_factor = 2

        # Dictionary to hold the loaded layers (farthest to closest)
        self.background_layers = {}

        # Load the background layers from 1.png to 10.png
        self._load_background_layers()

        # A list to hold the enemies on the client side
        self.enemies = []

    def _load_background_layers(self):
        """Loads background layers from 1.png to 10.png and handles missing files."""
        global sprites_folder
        local_sprites_folder = f"{sprites_folder}\\Game\\backgrounds"

        # Loop through 1 to 10 and load files if they exist
        for i in range(1, 11):
            try:
                filepath = os.path.join(local_sprites_folder, f"{i}.png")
                image = pygame.image.load(filepath).convert_alpha()  # Load with transparency
                image = self._scale_image_to_screen(image)  # Scale image to screen size
                self.background_layers[i] = {
                    'image': image,
                    'width': image.get_width()
                }
            except FileNotFoundError:
                print(f"File {i}.png not found, skipping.")
                continue

    def _scale_image_to_screen(self, image):
        """Helper method to scale an image to fit the entire screen size."""
        return pygame.transform.scale(image, (SCREEN_WIDTH * self.scale_factor, SCREEN_HEIGHT * self.scale_factor))

    def parallax_render(self, screen, player_position):
        """Renders the parallax scrolling background based on player's position."""
        # Define the parallax speed for each layer (closer layers move faster)
        parallax_speeds = {
            1: 0.1,  # Farthest layer (1.png)
            2: 0.2,
            3: 0.3,
            4: 0.4,
            5: 0.5,
            6: 0.6,
            7: 0.7,
            8: 0.8,
            9: 0.9,
            10: 1.0  # Closest layer (10.png)
        }

        # Render each layer with appropriate parallax speed
        for i in range(1, 11):
            if i in self.background_layers:
                layer = self.background_layers[i]['image']
                layer_width = self.background_layers[i]['width']
                parallax_speed = parallax_speeds.get(i, 1.0)
                offset = player_position.x * parallax_speed % layer_width
                self._render_layer(screen, layer, offset, layer_width, vertical_multiplier=(i * 0.1))

    def _render_layer(self, screen, layer, offset, layer_width, vertical_multiplier):
        """Helper method to render a background layer with a vertical offset based on depth."""
        vertical_offset = int(SCREEN_HEIGHT // 2 * vertical_multiplier)

        # Draw the layer twice to ensure continuous scrolling, with vertical adjustment
        screen.blit(layer, (-offset, -vertical_offset))  # Draw the layer starting at -offset and shifted up
        screen.blit(layer, (layer_width - offset, -vertical_offset))  # Draw the layer again to fill the gap

    def handle_click(self, position, mouse_side):
        mouse_click = pygame.mouse.get_pressed()
        if not self.in_options_menu and not self.paused:
            self.inventoryMenu.handle_mouse_input(position, mouse_side)

            # Check if the player just equipped a weapon
            if newClient.just_equipped:
                # Reset the flag and ignore this click for activating the weapon
                newClient.just_equipped = False
                return
            
            if newClient.current_weapon:
                newClient.activate_weapon()

        elif self.in_options_menu:
            mouse_pos = pygame.mouse.get_pos()
            self.optionMenu.handle_mouse_input(mouse_pos, mouse_click, mouse_click)

        elif self.paused:
            selected_option = self.pauseMenu.handle_mouse_input(position, pygame.mouse.get_pressed())
            if selected_option == "resume" and mouse_click[0]:
                self.paused = False
            elif selected_option == "options" and mouse_click[0]:
                self.in_options_menu = True
            elif selected_option == "logout" and mouse_click[0]:
                newClient.logout()
                global current_scene
                current_scene = MainMenu(self.screen)
                return

    def render_enemies(self):
        """Renders the enemies based on server data."""
        # Get enemy data from the server
        if newClient.server_data and newClient.server_data.enemy_data:
            # Clear existing enemies and update with server data
            self.enemies.clear()
            for id, enemy_data in newClient.server_data.enemy_data.items():
                if id in newClient.already_hit:
                    continue
                # Create an Enemy instance based on the server data
                realpos = CalculateScreenPosition(enemy_data['position'], newClient.position)
                enemy = Enemy(
                    position=pygame.Vector2(realpos.x, realpos.y),
                    health=enemy_data['health'],
                    is_server=False
                )
                enemy.current_frame_index = enemy_data['animation_frame']  # Set the correct frame
                enemy.current_animation = enemy_data['current_animation']
                # Load the appropriate animation based on the current state
                enemy.load_animation(enemy.current_animation)
                enemy.last_frame_time = pygame.time.get_ticks()
                enemy.frame_delay = 100
                
                self.enemies.append(enemy)

        # Render each enemy on the screen
        for enemy in self.enemies:
            try:
                enemy.render(self.screen)
            except:
                pygame.draw.rect(screen, RED, pygame.Rect(realpos.x, realpos.y, 128, 128))

    def render(self):
        global running
        global dt
        global current_music

        pygame.mixer.music.stop()
        current_music = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.in_options_menu:
                    self.in_options_menu = False  # Exit options menu
                else:
                    self.paused = not self.paused  # Toggle pause
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                debugger.toggle_debug()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event.pos, event.button)

        # Game rendering logic
        self.parallax_render(screen, newClient.position)

        if self.paused:
            newClient.movement_disabled = True
        else:
            newClient.movement_disabled = False

        # Update the player
        newClient.update(self.screen, dt)

        # Display debug information
        debugger.display_debug_info(self.screen, newClient.connectionInfo(), newClient=newClient)

        # Render enemies from server data
        self.render_enemies()

        if not self.paused and not self.in_options_menu:
            self.inventoryMenu.render(self.screen)

        if self.paused and not self.in_options_menu:
            self.pauseMenu.render(self.screen)
        elif self.in_options_menu:
            self.optionMenu.render(self.screen)

        dt = clock.tick(60) / 1000

class ServerSelect(Scene):
    def __init__(self, screen):
        super().__init__(screen)
        self.username = ""  # Store username input
        self.custom_server = ""  # Store custom server IP
        self.active_input = None  # Tracks which input box is active ('username' or 'custom_server')
        self.servers = []  # List of discovered servers
        self.selected_server = None  # Selected server
        self.lock = threading.Lock()  # Lock for managing server list updates

        # Start asynchronous server discovery
        threading.Thread(target=discover_servers_async, args=(self.servers, self.lock), daemon=True).start()
        self.frame_index = 0
        self.frames = []
        self.frame_delay = 75  # Delay in milliseconds between frames
        self.last_frame_update = pygame.time.get_ticks()  # Time of the last frame update

        global sprites_folder
        # Vaporwave aesthetic colors and fonts
        self.button_color = (85, 255, 255)
        self.hover_color = (255, 51, 153)
        self.text_color = (255, 153, 0)
        self.input_box_color = (255, 255, 255)
        self.disabled_color = (128, 128, 128)

        self.font = pygame.font.Font((f"{sprites_folder}\Fonts\\retro_font.ttf"), int(self.screen_height * 0.03))
        self.title_font = pygame.font.Font((f"{sprites_folder}\Fonts\\retro_font.ttf"), int(self.screen_height * 0.03))

        # Load all the frames from the GIF-like images
        self.load_frames_from_folder(f"{sprites_folder}\Game\menu_background")

    def load_frames_from_folder(self, folder_path):
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".png"):
                frame = pygame.image.load(os.path.join(folder_path, filename)).convert_alpha()
                scaled_frame = pygame.transform.scale(frame, (self.screen_width, self.screen_height))
                self.frames.append(scaled_frame)

    def draw_text_with_shadow(self, screen, text, font: pygame.font.Font, text_color, shadow_color, position, shadow_offset=5):
        shadow_text = font.render(text, True, shadow_color)
        shadow_rect = shadow_text.get_rect(center=(position[0] + shadow_offset, position[1] + shadow_offset))
        screen.blit(shadow_text, shadow_rect)

        main_text = font.render(text, True, text_color)
        main_rect = main_text.get_rect(center=position)
        screen.blit(main_text, main_rect)

    def draw_button(self, screen, rect, text, hover):
        color = self.hover_color if hover else self.button_color
        pygame.draw.rect(screen, color, rect, border_radius=10)
        glow_rect = rect.inflate(20, 20)
        glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*color, 128), glow_surface.get_rect(), border_radius=10)
        screen.blit(glow_surface, glow_rect.topleft)

        shadow_color = (0, 0, 0)  # Black shadow
        self.draw_text_with_shadow(screen, text, self.font, self.text_color, shadow_color, rect.center)

    def draw_input_box(self, screen, label, rect, text, active):
        shadow_color = (0, 0, 0)
        label_position = (rect.x + rect.width // 2, rect.y - rect.height // 1.5)
        self.draw_text_with_shadow(screen, label, self.font, self.text_color, shadow_color, label_position, shadow_offset=3)
        border_thickness = 3 if active else 1
        pygame.draw.rect(screen, self.input_box_color, rect, border_thickness, border_radius=10)
        text_position = (rect.x + 10, rect.y + rect.height // 2)
        text_surface = self.font.render(text, True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(rect.x + 10, rect.y + rect.height // 2))
        screen.blit(text_surface, text_rect)


    def handle_click(self, position):
        input_box = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.4, self.screen_width * 0.3, self.screen_height * 0.07)
        custom_server_box = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.55, self.screen_width * 0.3, self.screen_height * 0.07)
        join_button = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.75, self.screen_width * 0.3, self.screen_height * 0.08)
        back_button = pygame.Rect(self.screen_width * 0.05, self.screen_height * 0.8, self.screen_width * 0.2, self.screen_height * 0.08)
        add_server_button = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.65, self.screen_width * 0.3, self.screen_height * 0.08)

        if input_box.collidepoint(position):
            self.active_input = 'username'
        elif custom_server_box.collidepoint(position):
            self.active_input = 'custom_server'
        else:
            self.active_input = None  # No input box clicked

        if back_button.collidepoint(position):
            global current_scene
            current_scene = MainMenu(self.screen)
            return

        if join_button.collidepoint(position) and self.selected_server:
            serverIp = self.selected_server.split("\n")[1]
            newClient.username = self.username
            newClient.connectToServer(ip=serverIp)
            current_scene = Gameplay(self.screen)
            return

        if add_server_button.collidepoint(position) and is_valid_ip(self.custom_server):
            with self.lock:
                self.servers.append(f"Custom Server\n{self.custom_server}")
            self.custom_server = ""  # Clear input after adding the server

        for i, server in enumerate(self.servers):
            server_rect = pygame.Rect(self.screen_width * 0.05, self.screen_height * (0.2 + i * 0.1), self.screen_width * 0.4, self.screen_height * 0.08)
            if server_rect.collidepoint(position):
                self.selected_server = server

    def render(self):
        global running
        current_time = pygame.time.get_ticks()

        if current_time - self.last_frame_update > self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_frame_update = current_time

        shadow_color = (0, 0, 0)
        title_color = (255, 102, 204)  # Neon pink for title

        # Button dimensions
        button_width, button_height = self.screen_width * 0.3, self.screen_height * 0.08

        # Button positions
        join_button = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.75, button_width, button_height)
        back_button = pygame.Rect(self.screen_width * 0.05, self.screen_height * 0.8, self.screen_width * 0.2, button_height)
        add_server_button = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.65, button_width, button_height)

        screen.blit(self.frames[self.frame_index], (0, 0))

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                self.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN and self.active_input:
                if event.key == pygame.K_BACKSPACE:
                    if self.active_input == 'username':
                        self.username = self.username[:-1]
                    elif self.active_input == 'custom_server':
                        self.custom_server = self.custom_server[:-1]
                else:
                    if event.unicode.isprintable():
                        if self.active_input == 'username':
                            self.username += event.unicode
                        elif self.active_input == 'custom_server':
                            self.custom_server += event.unicode

        # Render title
        self.draw_text_with_shadow(screen, "Available Servers", self.title_font, title_color, shadow_color, (self.screen_width * 0.3, self.screen_height * 0.1))

        # Render buttons with hover effects and shadow text
        mouse_pos = pygame.mouse.get_pos()
        self.draw_button(screen, join_button, "Join", join_button.collidepoint(mouse_pos))
        self.draw_button(screen, back_button, "Back", back_button.collidepoint(mouse_pos))
        self.draw_button(screen, add_server_button, "Add Custom Server", add_server_button.collidepoint(mouse_pos))

        # Render input boxes
        username_box = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.4, button_width, button_height)
        custom_server_box = pygame.Rect(self.screen_width * 0.55, self.screen_height * 0.55, button_width, button_height)
        self.draw_input_box(screen, "Enter Username:", username_box, self.username, self.active_input == 'username')
        self.draw_input_box(screen, "Custom Server IP:", custom_server_box, self.custom_server, self.active_input == 'custom_server')

        # Render server list
        with self.lock:
            for i, server in enumerate(self.servers):
                server_rect = pygame.Rect(self.screen_width * 0.05, self.screen_height * (0.2 + i * 0.1), self.screen_width * 0.4, self.screen_height * 0.08)

                # Check if this server is selected, and change color accordingly
                if self.selected_server == server:
                    server_color = (255, 255, 102)  # Highlighted color for selected server
                else:
                    server_color = self.button_color

                pygame.draw.rect(screen, server_color, server_rect, border_radius=10)
                server_name = server.split("\n")[0]
                self.draw_text_with_shadow(screen, server_name, self.font, self.text_color, shadow_color, server_rect.center)

class OptionsScene(Scene):
    def __init__(self, screen):
        super().__init__(screen)
        self.fullscreen = fullscreen  # Assume fullscreen is a global variable
        self.back_button = None

    def render(self):
        global running
        global current_scene
        global volume

        background_color = (30, 30, 30)
        button_color = (50, 150, 255)
        button_hover_color = (70, 170, 255)
        text_color = (255, 255, 255)

        screen.fill(background_color)

        # Set up fonts
        font = pygame.font.Font(None, int(self.screen_height * 0.05))

        # Volume slider text
        volume_text = font.render(f"Volume: {volume}", True, text_color)
        volume_rect = pygame.Rect((self.screen_width / 2 - 100, self.screen_height * 0.3, 200, 10))
        pygame.draw.rect(screen, (255, 255, 255), volume_rect)

        volume_slider_pos = int(volume_rect.x + (volume / 100) * volume_rect.width)
        pygame.draw.circle(screen, (255, 0, 0), (volume_slider_pos, volume_rect.y + 5), 8)

        screen.blit(volume_text, (self.screen_width / 2 - 100, self.screen_height * 0.2))

        # Fullscreen toggle button
        toggle_text = "Fullscreen: On" if self.fullscreen else "Fullscreen: Off"
        toggle_surf = font.render(toggle_text, True, text_color)
        toggle_rect = toggle_surf.get_rect(center=(self.screen_width / 2, self.screen_height * 0.5))
        pygame.draw.rect(screen, (255, 255, 255), toggle_rect.inflate(20, 10), 2)
        screen.blit(toggle_surf, toggle_rect)

        # Back button
        back_text = font.render("Back", True, text_color)
        back_rect = pygame.Rect(self.screen_width / 2 - 100, self.screen_height * 0.7, 200, 50)
        if back_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(screen, button_hover_color, back_rect)
        else:
            pygame.draw.rect(screen, button_color, back_rect)

        screen.blit(back_text, (self.screen_width / 2 - back_rect.width / 4, self.screen_height * 0.7 + back_rect.height / 4))

        # Store rects for later use
        self.volume_rect = volume_rect
        self.toggle_rect = toggle_rect
        self.back_button = back_rect

        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                if self.volume_rect.collidepoint(event.pos):
                    relative_x = event.pos[0] - self.volume_rect.x
                    volume = max(0, min(100, int((relative_x / self.volume_rect.width) * 100)))
                elif self.toggle_rect.collidepoint(event.pos):
                    self.fullscreen = not self.fullscreen
                    pygame.display.toggle_fullscreen()
                elif self.back_button.collidepoint(event.pos):
                    current_scene = MainMenu(screen)
                    return

    def handle_click(self, position):
        pass

class MainMenu(Scene):
    def __init__(self, screen):
        super().__init__(screen)
        self.frame_index = 0
        self.frames = []
        self.frame_delay = 75  # Delay in milliseconds between frames
        self.last_frame_update = pygame.time.get_ticks()  # Time of the last frame update

        global sprites_folder
        # color scheme for vaporwave aesthetics
        self.button_color = (85, 255, 255)
        self.hover_color = (255, 51, 153) 
        self.text_color = (255, 153, 0)
        self.font = pygame.font.Font((f"{sprites_folder}\Fonts\\retro_font.ttf"), int(self.screen_height * 0.025))
        self.title_font = pygame.font.Font((f"{sprites_folder}\Fonts\\retro_font.ttf"), int(self.screen_height * 0.055))
        
        # Load all the frames from the GIF-like images
        self.load_frames_from_folder(f"{sprites_folder}\Game\menu_background")

    def load_frames_from_folder(self, folder_path):
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".png"):
                frame = pygame.image.load(os.path.join(folder_path, filename)).convert_alpha()
                scaled_frame = pygame.transform.scale(frame, (self.screen_width, self.screen_height))
                self.frames.append(scaled_frame)

    def draw_text_with_shadow(self, screen, text, font, text_color, shadow_color, position, shadow_offset=5):
        """
        Draws text with a drop shadow effect.
        
        Args:
        - screen: The pygame screen surface where the text will be rendered.
        - text: The text to render.
        - font: The font object to use for the text rendering.
        - text_color: Color of the main text.
        - shadow_color: Color of the shadow text.
        - position: A tuple (x, y) for the center position of the text.
        - shadow_offset: The offset for the shadow (default is 5 pixels).
        """
        # Render shadow text (offset by shadow_offset pixels)
        shadow_text = font.render(text, True, shadow_color)
        shadow_rect = shadow_text.get_rect(center=(position[0] + shadow_offset, position[1] + shadow_offset))
        screen.blit(shadow_text, shadow_rect)

        # Render the main text on top
        main_text = font.render(text, True, text_color)
        main_rect = main_text.get_rect(center=position)
        screen.blit(main_text, main_rect)

    def draw_button(self, screen, rect, text, hover):
        color = self.hover_color if hover else self.button_color
        # Draw a rectangle with rounded corners (glow effect)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        # Outer glow
        glow_rect = rect.inflate(20, 20)
        glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*color, 128), glow_surface.get_rect(), border_radius=10)
        screen.blit(glow_surface, glow_rect.topleft)

        # Use draw_text_with_shadow to render text with shadow on the button
        shadow_color = (0, 0, 0)  # Black shadow
        self.draw_text_with_shadow(screen, text, self.font, self.text_color, shadow_color, rect.center, shadow_offset=3)


    def handle_click(self, position):
        pass

    def render(self):
        global running
        global current_scene
        global current_music

        if current_music != "menu.mp3":
            SwitchMusic("menu.mp3", True)

        current_time = pygame.time.get_ticks()

        if current_time - self.last_frame_update > self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.frames)  # Loop back to the first frame
            self.last_frame_update = current_time  # Update the time of the last frame change

        shadow_color = (0, 0, 0)
        title_color = (255, 102, 204)  # Neon pink for title

        # Button dimensions
        button_width, button_height = self.screen_width * 0.3, self.screen_height * 0.1
        button_vertical_offset = 30

        # Button positions
        server_select_rect = pygame.Rect(
            (self.screen_width / 2 - button_width / 2, self.screen_height / 2 - button_height / 2 + button_vertical_offset),
            (button_width, button_height)
        )
        options_rect = pygame.Rect(
            (self.screen_width / 2 - button_width / 2, self.screen_height / 2 - button_height / 2 + button_height * 1.5 + button_vertical_offset),
            (button_width, button_height)
        )
        exit_rect = pygame.Rect(
            (self.screen_width / 2 - button_width / 2, self.screen_height / 2 - button_height / 2 + button_height * 3 + button_vertical_offset),
            (button_width, button_height)
        )

        # Handle events and check for mouse hover
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                if server_select_rect.collidepoint(event.pos):
                    current_scene = ServerSelect(screen)
                    return
                elif options_rect.collidepoint(event.pos):  # Redirect to Options scene
                    current_scene = OptionsScene(screen)
                    return
                elif exit_rect.collidepoint(event.pos):
                    running = False
                    return

        # Render background
        screen.blit(self.frames[self.frame_index], (0, 0))

        # Render title
        self.draw_text_with_shadow(screen, str.upper(GAME_NAME), self.title_font, title_color, shadow_color, (self.screen_width / 2, self.screen_height * 0.2))

        # Draw buttons with hover effects
        self.draw_button(screen, server_select_rect, "Join a Server", server_select_rect.collidepoint(mouse_pos))
        self.draw_button(screen, options_rect, "Options", options_rect.collidepoint(mouse_pos))
        self.draw_button(screen, exit_rect, "Exit", exit_rect.collidepoint(mouse_pos))

current_scene = MainMenu(screen)

while running:
    pygame.mixer.music.set_volume(volume / 100)
    if current_scene:  
        current_scene.update()
    else:
        break

pygame.quit()
newClient.disconnectFromServer()
os._exit(0)