import socket, struct
import threading, json, time, re, os
import pygame
from pathlib import Path
from abc import ABC, abstractmethod

from typing import Dict, Optional, List, Tuple
from collections import deque

from GameConstants import *
from Weapons import *

## Some global variables that need to be defined early
volume = 15
fullscreen = True

## Networking functions and classes
class NetworkClient:
    """
    A client class that handles client connections to the server.\n
    Stores and receives data from the server.\n
    Only meant to be used indirectly through GameClient.
    """

    def __init__(self, gameClient: 'GameClient', host: str = "127.0.0.1", port: int = 44200):
        # basic server stuff
        self.host = host
        self.port = port
        self.gameClient = gameClient

        # for reconnection
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
            # close if server sends close command
            if "[CLOSECONNECTION]" in serverData.decode('utf-8'): # this is a stupid way to do this
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

        # If we reach max attempts, show a failure message
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
        data_dict = {
            "username": packet.username,
            "position": {"x": packet.position.x, "y": packet.position.y},
            "gameData": {"HP": packet.gameData.HP}
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
    
    def deserialize_server_data(self, data: bytes):
        """
        Deserializes the server packet from the server.
        """
        data_dict = json.loads(data.decode('utf-8'))
        return ServerPacket(
            terrain=data_dict["terrain"],
            clients_data=data_dict["clients_data"]
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

        self.current_weapons: Weapon = None

        self.connInfo = {
            "ip": None, 
            "port": None
        }

        self.message: Optional[Message] = None  # Add message attribute for server messages like disconnects

        # Spawn the player above the center of the ground
        self.spawn(0, 400)

    def connectToServer(self, ip: str = "127.0.0.1", port: int = 44200):
        """Creates a network client and attempts to connect to the given server"""
        self.connInfo["ip"], self.connInfo["port"] = ip, port
        self.message = None
        self.networkClient = NetworkClient(self, ip, port)

    def logout(self):
            """Resets the game state and disconnects from the server."""
            self.position = pygame.Vector2(0, 0)
            self.velocity = 5
            self.velocity_y = 0
            self.worldObjects = [] 
            self.server_data = None 

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
        player_rect = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2, PLAYER_WIDTH, PLAYER_HEIGHT)
        try:
            terrain = self.server_data.terrain
            self.grounded = False

            for i in range(len(terrain) - 1):
                line_start = pygame.Vector2(terrain[i])
                line_end = pygame.Vector2(terrain[i + 1])

                # Convert to screen coordinates for collision detection
                screen_line_start = CalculateScreenPosition(line_start, self.position)
                screen_line_end = CalculateScreenPosition(line_end, self.position)

                if line_rect_collision(screen_line_start, screen_line_end, player_rect):
                    slope = (line_end.y - line_start.y) / (line_end.x - line_start.x + 0.01)
                    # Smooth player movement based on slope
                    target_y = min(line_start.y, line_end.y) - PLAYER_HEIGHT // 2

                    buffer = 5  # A small buffer of 5 pixels for detection
                    if self.position.y + buffer >= target_y:  
                        self.grounded = True

                    # Smooth snapping to ground
                    self.position.y += (target_y - self.position.y) * 0.2

                    # Adjust velocity based on slope (reduce gravity effect when climbing)
                    if abs(slope) > 0:
                        self.velocity_y = -self.velocity * slope * 0.5 

                    # Stop falling when grounded
                    if abs(self.position.y - target_y) < 1:  # Small tolerance to ensure proper grounding
                        self.velocity_y = 0
                    return True

            return False
        except:
            return False

    def apply_gravity(self, dt):
        if not self.grounded:
            self.velocity_y += GRAVITY * dt
            self.position.y += self.velocity_y * dt
        else:
            self.velocity_y = 0  # Reset vertical velocity if grounded

    def handleMovement(self, keys):
        if self.movement_disabled:
            return

        moveVector = pygame.Vector2(0, 0)
        
        # Horizontal movement
        if keys[pygame.K_a]:
            moveVector.x -= self.velocity
        if keys[pygame.K_d]:
            moveVector.x += self.velocity

        # Update the player's position with movement boundaries
        #TODO: Fix boundaries
        ## I don't understand this TODO anymore
        self.position.x = max(-3000, min(3000, self.position.x + moveVector.x))

        # Jumping logic
        if keys[pygame.K_SPACE] and self.grounded:
            self.velocity_y = -65 * self.velocity
            self.grounded = False

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

    def draw(self, screen):
        # always draw the player at 0,0 (center of screen, not actual 0,0). move world around player to emulate camera
        player = pygame.draw.rect(screen, BLUE, pygame.Rect(SCREEN_WIDTH//2 - PLAYER_WIDTH//2, SCREEN_HEIGHT//2 - PLAYER_HEIGHT//2, PLAYER_WIDTH, PLAYER_HEIGHT))

        # render the player's name above the player
        font = pygame.font.SysFont(None, 40)
        text = font.render(self.username, True, BLACK)
        text_rect = text.get_rect(center=(player.x + PLAYER_WIDTH//2, player.y - 20))
        screen.blit(text, text_rect)

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
        try:
            terrain = self.server_data.terrain
            adjusted_points: List[pygame.Vector2] = [CalculateScreenPosition(pygame.Vector2(x, y), self.position) for x, y in terrain]
            lowered_points = [pygame.Vector2(x+150, y+150) for x, y in adjusted_points]
            # basically draw the terrain to the bottom of the screen
            # consider fullscreen being 60 taller
            adjusted_points.append((adjusted_points[-1][0], SCREEN_HEIGHT))
            adjusted_points.append((adjusted_points[0][0], SCREEN_HEIGHT))

            if fullscreen == False:
                lowered_points.append((lowered_points[-1][0], SCREEN_HEIGHT))
                lowered_points.append((lowered_points[0][0], SCREEN_HEIGHT))
            else:
                lowered_points.append((lowered_points[-1][0], SCREEN_HEIGHT + 60))
                lowered_points.append((lowered_points[0][0], SCREEN_HEIGHT + 60))

            pygame.draw.polygon(screen, DARK_GREEN, adjusted_points)
            pygame.draw.polygon(screen, DIRT_BROWN, lowered_points)
        except:
            pass

    def drawOtherClients(self, screen):
        if not self.server_data:
            return
        
        clients_data = json.loads(self.server_data.clients_data)
        for client in clients_data:
            if clients_data[client] == None:
                continue
            client = json.loads(clients_data[client])

            clientPosition = client['position']
            screenPosition = CalculateScreenPosition(pygame.Vector2(clientPosition['x'], clientPosition['y']), self.position)

            # Draw the other client's representation (e.g., a rectangle)
            player = pygame.draw.rect(screen, GREEN, (
                screenPosition.x - PLAYER_WIDTH // 2,
                screenPosition.y - PLAYER_HEIGHT // 2,
                PLAYER_WIDTH, PLAYER_HEIGHT
            ))

            font = pygame.font.SysFont(None, 40)
            text = font.render(client['username'], True, BLACK)
            text_rect = text.get_rect(center=(player.x + PLAYER_WIDTH//2, player.y - 20))
            screen.blit(text, text_rect)

    def spawn(self, spawn_x: int = 0, spawn_height: int = 100):
        """
        Spawns the player at a given location, where 0,0 is the center of the world.
        """
        self.position = pygame.Vector2(spawn_x, -spawn_height) 
        self.velocity_y = 0
        self.grounded = False

    def equip_weapon(self, weapon: 'Weapon'):
        """Equips a weapon for the player."""
        if self.current_weapon:
            self.current_weapon.unequipped(self)
        self.current_weapon = weapon
        self.current_weapon.equipped(self)

    def unequip_weapon(self):
        """Unequips the current weapon, if any."""
        if self.current_weapon:
            self.current_weapon.unequipped(self)
            self.current_weapon = None

    def activate_weapon(self):
        """Activates the currently equipped weapon, if any."""
        if self.current_weapon:
            self.current_weapon.activated(self)

    def update(self, screen, dt):
        self.apply_gravity(dt)
        self.handleMovement(pygame.key.get_pressed())
        self.detect_collision()

        if self.position.y > SCREEN_HEIGHT:  # If the player falls too far
            self.spawn(100)

        self.drawTerrain(screen)
        self.drawWorldObjects(screen)
        self.draw(screen)
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

newClient = GameClient(GameData(HP=100), "User1", pygame.Vector2(0, 0))

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
        
        # Key tracking
        self.key_states: Dict[int, DebugKeyState] = {}
        self.key_history: List[Tuple[int, str, float]] = []
        self.max_key_history = 10
        
        # Performance metrics
        self.frame_times = deque(maxlen=60)
        self.last_frame_time = time.time()
        
        # Network metrics
        self.last_ping: Optional[str] = None
        self.ping_interval = 2.0
        self.last_ping_time = 0
    
    def ping_server(self, hostname: str, port: int) -> str:
        """Ping server and return latency in milliseconds"""
        try:
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
        try:
            clients_data = json.loads(newClient.server_data.clients_data)
            for client in clients_data:
                # Convert string to dictionary
                if clients_data[client] == None:
                    continue
                client_data = json.loads(clients_data[client])
                username = client_data["username"]
                
                # Display client info
                client_lines = [
                    f"User: {username}",
                    f"IP: {client}",
                    "---"
                ]
                
                for line in client_lines:
                    text_surface = self.font.render(line, True, self.text_color)
                    screen.blit(text_surface, (x_offset, y_offset))
                    y_offset += self.font_size
                
                # Add spacing between clients
                y_offset += self.font_size // 2
                
        except AttributeError:
            # Handle case where allClients might not be available
            error_text = self.font.render("No client data available", True, self.text_color)
            screen.blit(error_text, (x_offset, y_offset))
    
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
    
    def track_key_event(self, event: pygame.event.Event) -> None:
        """Track key press/release events and durations"""
        current_time = time.time()
        
        if event.type == pygame.KEYDOWN:
            if event.key not in self.key_states:
                self.key_states[event.key] = DebugKeyState(
                    is_pressed=True,
                    press_time=current_time,
                    release_time=0,
                    hold_duration=0,
                    press_count=1
                )
            else:
                self.key_states[event.key].is_pressed = True
                self.key_states[event.key].press_time = current_time
                self.key_states[event.key].press_count += 1
            
            self.key_history.append((event.key, "pressed", current_time))
        
        elif event.type == pygame.KEYUP:
            if event.key in self.key_states:
                state = self.key_states[event.key]
                state.is_pressed = False
                state.release_time = current_time
                state.hold_duration = current_time - state.press_time
            
            self.key_history.append((event.key, "released", current_time))
        
        while len(self.key_history) > self.max_key_history:
            self.key_history.pop(0)
    
    def get_active_keys(self) -> List[str]:
        """Return list of currently held keys"""
        return [pygame.key.name(key) for key, state in self.key_states.items() 
                if state.is_pressed]
    
    def get_key_stats(self, key: int) -> Optional[DebugKeyState]:
        """Get detailed stats for a specific key"""
        return self.key_states.get(key)
    
## Pygame setup
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags=pygame.FULLSCREEN)
current_scene = None
clock = pygame.time.Clock()
running = True
dt = 0
debugger = Debugger()

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
    def __init__(self, inventory_items: list, columns: int = 5, rows: int = 5, cell_size: int = 64, padding: int = 10):
        super().__init__(title="Inventory", options=inventory_items)
        self.columns = columns
        self.rows = rows
        self.cell_size = cell_size
        self.padding = padding
        self.position = (0, 0)

    def set_position(self, screen):
        self.position = (screen.get_width() - (self.columns * (self.cell_size + self.padding)) - 20, screen.get_height() - (self.rows * (self.cell_size + self.padding)) - 20)

    def on_select(self, selected_option: int):
        selected_item = self.options[selected_option]
        print(f"Selected item: {selected_item}")

    def render(self, screen):
        self.set_position(screen)

        # Create a transparent surface for the inventory background
        background_width = self.columns * (self.cell_size + self.padding) + 20
        background_height = self.rows * (self.cell_size + self.padding) + 20
        background = pygame.Surface((background_width, background_height), pygame.SRCALPHA)
        background.fill((0, 0, 0, 128))  # Semi-transparent background

        # Blit the background onto the screen
        screen.blit(background, (self.position[0] - 10, self.position[1] - 10))

        font = pygame.font.SysFont(None, 30)

        # Calculate grid placement
        self.option_rects = []
        for idx, option in enumerate(self.options):
            col = idx % self.columns
            row = idx // self.columns
            x = self.position[0] + col * (self.cell_size + self.padding)
            y = self.position[1] + row * (self.cell_size + self.padding)

            # Draw the cell as a rectangle
            cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
            pygame.draw.rect(screen, (255, 255, 255), cell_rect, 2)

            # Render the item (text-based placeholder for now)
            option_surf = font.render(option, True, (255, 255, 255))
            option_rect = option_surf.get_rect(center=cell_rect.center)
            screen.blit(option_surf, option_rect)

            self.option_rects.append(cell_rect)

    def handle_mouse_input(self, mouse_pos, mouse_click):
        for idx, option_rect in enumerate(self.option_rects):
            if option_rect.collidepoint(mouse_pos):
                self.active_option = idx
                if mouse_click[0]:
                    self.on_select(idx)

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
            print(volume)

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
        self.inventoryMenu = InventoryMenu(["Sword", "Shield", "Potion"])
        self.pauseMenu = PauseMenu(["Resume", "Options", "Log Out"])  # Added "Options" button
        self.optionMenu = OptionMenu()  # Create the OptionMenu

    def handle_click(self, position):
        if self.in_options_menu:
            mouse_click = pygame.mouse.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            self.optionMenu.handle_mouse_input(mouse_pos, mouse_click, mouse_click)
        elif self.paused:
            selected_option = self.pauseMenu.handle_mouse_input(position, pygame.mouse.get_pressed())
            if selected_option == "resume":
                self.paused = False
            elif selected_option == "options":
                self.in_options_menu = True
            elif selected_option == "logout":
                newClient.logout()
                global current_scene
                current_scene = MainMenu(self.screen)
                return

    def render(self):
        global running
        global dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.in_options_menu:
                    self.in_options_menu = False  # Exit options menu
                else:
                    self.paused = not self.paused  # Toggle pause
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event.pos)

        # Game rendering logic
        self.screen.fill(LIGHT_BLUE)

        if self.paused:
            newClient.movement_disabled = True
        else:
            newClient.movement_disabled = False

        newClient.update(self.screen, dt)
        debugger.display_debug_info(self.screen, newClient.connectionInfo(), newClient=newClient)

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
            elif event.type == pygame.MOUSEBUTTONDOWN:
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
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