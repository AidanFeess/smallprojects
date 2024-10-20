import socket, struct
import threading, json, time, re
import pygame
from abc import ABC, abstractmethod

from typing import Dict, Optional, List, Tuple
from collections import deque

from GameConstants import *
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
        buffer = ""
        while self.connected:
            try:
                # Create the packet before sending
                newPacket = self.serialize_client_data(
                    ClientPacket(
                        username=self.gameClient.username,
                        position=self.gameClient.position,
                        gameData=self.gameClient.gameData
                    )
                )

                # Send the packet with a length prefix
                self.send_with_length_prefix(newPacket)
                 # Receive data from the server
                rawdata = self.connection.recv(10240)
                self.gameClient.server_data = self.deserialize_server_data(rawdata)

                if not rawdata:
                    break  # Server closed the connection
                
                time.sleep(0.01)  # send data every 100 ms

            except (socket.error, OSError) as e:
                print(f"Network error: {e}. Attempting to reconnect...")
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
        while not self.connected and self.reconnect_attempts < 5:  # Try up to 5 reconnection attempts
            self.reconnect_attempts += 1

            try:
                time.sleep(2)  # Wait 2 seconds between attempts
                if self.connect_to_server() == False:
                    return

            except Exception as e:
                print(f"Reconnect attempt failed: {e}")

        if not self.connected:
            print("Failed to reconnect after 5 attempts. Disconnecting.")
            self.disconnect()

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
    """
    def __init__(self, gameData: GameData, username: str = "Guest", position: Position = (0, 0)):
        self.gameData = gameData
        self.username = username
        self.position = position
        self.worldObjects = []
        self.server_data: ServerPacket = {}
        self.velocity = 5  # Horizontal movement speed
        self.velocity_y = 0  # Vertical velocity (gravity impact)
        self.grounded = False  # Is the player grounded?

        self.connInfo = {
            "ip": None, 
            "port": None
        }

        # Spawn the player 100 pixels above the ground
        self.spawn(400)

    def connectToServer(self, ip: str = "127.0.0.1", port: int = 44200):
        """Creates a network client and attempts to connect to the given server"""
        self.connInfo["ip"], self.connInfo["port"] = ip, port
        self.networkClient = NetworkClient(self, ip, port)

    def connectionInfo(self) -> tuple[str, int]:
        """Returns the GameClient's server connection info"""
        return (self.connInfo["ip"], self.connInfo["port"])

    def disconnectFromServer(self):
        if not self.networkClient:
            return
        self.networkClient.disconnect()

    def detect_collision(self):
        player_rect = pygame.Rect(SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2, PLAYER_WIDTH, PLAYER_HEIGHT)
        try:
            terrain = self.server_data.terrain

            self.grounded = False

            for i in range(len(terrain) - 1):
                line_start = pygame.Vector2(terrain[i])
                line_end = pygame.Vector2(terrain[i + 1])

                # Adjust these to screen coordinates only for drawing or hit testing
                screen_line_start = CalculateScreenPosition(line_start, self.position)
                screen_line_end = CalculateScreenPosition(line_end, self.position)

                if line_rect_collision(screen_line_start, screen_line_end, player_rect):
                    self.grounded = True
                    self.velocity_y = 0  # Stop falling
                    self.position.y = min(line_start.y, line_end.y) - PLAYER_HEIGHT // 2  # Snap player to world terrain
                    return True

            return False
        except:
            return False

    def apply_gravity(self, dt):
        # Only apply gravity if the player is not grounded
        if not self.grounded:
            self.velocity_y += GRAVITY * dt  # Apply gravity to vertical velocity

        # Apply vertical movement based on velocity
        self.position.y += self.velocity_y * dt

    def handleMovement(self, keys):
        moveVector = pygame.Vector2(0, 0)
        if keys[pygame.K_w]:
            moveVector.y -= self.velocity  # Move up (decrease y)
        if keys[pygame.K_s]:
            moveVector.y += self.velocity  # Move down (increase y)
        if keys[pygame.K_a]:
            moveVector.x -= self.velocity  # Move left (decrease x)
        if keys[pygame.K_d]:
            moveVector.x += self.velocity  # Move right (increase x)

        # Update the player's position
        self.position += moveVector

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
            # Calculate the screen position relative to player's current position
            screenPosition = CalculateScreenPosition(obj.worldPosition, self.position)

            # Draw objects based on their type
            if obj.objectType.isSprite and obj.sprite:
                # Draw the sprite
                screen.blit(obj.sprite.image, (screenPosition.x, screenPosition.y))
            elif obj.objectType.isCircle:
                # Draw a circle
                pygame.draw.circle(screen, obj.color, (screenPosition.x, screenPosition.y), obj.width)
            elif obj.objectType.isRect:
                # Draw a rectangle, ensuring it's centered
                pygame.draw.rect(screen, obj.color, (screenPosition.x - obj.width // 2, screenPosition.y - obj.height // 2, obj.width, obj.height))

    def drawTerrain(self, screen):
        try:
            terrain = self.server_data.terrain
            adjusted_points: List[pygame.Vector2] = [CalculateScreenPosition(pygame.Vector2(x, y), self.position) for x, y in terrain]
            # basically draw the terrain to the bottom of the screen
            adjusted_points.append((adjusted_points[-1][0], SCREEN_HEIGHT))
            adjusted_points.append((adjusted_points[0][0], SCREEN_HEIGHT))


            pygame.draw.polygon(screen, (0, 200, 0), adjusted_points)
        except:
            pass

    def drawOtherClients(self, screen):
        if not self.server_data:
            return
        
        clients_data = json.loads(self.server_data.clients_data)
        for client in clients_data:
            # Convert string to dictionary
            if clients_data[client] == None:
                continue
            client = json.loads(clients_data[client])

            # Get the client position and convert to screen coordinates
            clientPosition = client['position']
            screenPosition = CalculateScreenPosition(pygame.Vector2(clientPosition['x'], clientPosition['y']), self.position)

            # Draw the other client's representation (e.g., a rectangle)
            player = pygame.draw.rect(screen, GREEN, (
                screenPosition.x - PLAYER_WIDTH // 2,  # X coordinate
                screenPosition.y - PLAYER_HEIGHT // 2,  # Y coordinate
                PLAYER_WIDTH, PLAYER_HEIGHT  # Width and Height of the client rectangle
            ))

            font = pygame.font.SysFont(None, 40)
            text = font.render(client['username'], True, BLACK)
            text_rect = text.get_rect(center=(player.x + PLAYER_WIDTH//2, player.y - 20))
            screen.blit(text, text_rect)

    def spawn(self, spawn_height: int = 100):
        """
        Spawns the player a certain height above the terrain.
        """
        self.position = pygame.Vector2(0, -spawn_height)  # Spawn the player at (0, -spawn_height) relative to the world
        self.velocity_y = 0  # Reset vertical velocity
        self.grounded = False  # Player is not grounded initially

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

newClient = GameClient(GameData(HP=100), "User1", pygame.Vector2(0, 50))

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
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
current_scene = None
clock = pygame.time.Clock()
running = True
dt = 0
debugger = Debugger()
discoverThread = None

## Pygame Functions
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

    def handle_click(self, position):
        pass

    def render(self):
        global running
        global dt

        for event in pygame.event.get():
            debugger.track_key_event(event)
            if event.type == pygame.QUIT:
                running = False

        screen.fill(LIGHT_BLUE)

        newClient.update(screen, dt)
        
        debugger.display_debug_info(screen, (newClient.connectionInfo()[0], newClient.connectionInfo()[1]), newClient=newClient)
        
        pygame.display.flip()    
        dt = clock.tick(60) / 1000

class ServerSelect(Scene):
    def __init__(self, screen):
        super().__init__(screen)

    def handle_click(self, position):
        pass

    def render(self):
        global running
        global current_scene

        # Set up colors
        background_color = (30, 30, 30)
        text_color = (255, 255, 255)
        button_color = (50, 150, 255)
        button_hover_color = (70, 170, 255)
        input_box_color = (255, 255, 255)
        disabled_color = (128, 128, 128)

        # Get screen dimensions
        screen_width, screen_height = screen.get_size()

        # Set up fonts
        font = pygame.font.Font(None, int(screen_height * 0.05))
        title_font = pygame.font.Font(None, int(screen_height * 0.07))

        # Username entry box setup
        input_box = pygame.Rect(screen_width * 0.55, screen_height * 0.4, screen_width * 0.3, screen_height * 0.07)
        custom_server_box = pygame.Rect(screen_width * 0.55, screen_height * 0.55, screen_width * 0.3, screen_height * 0.07)
        username = ""
        custom_server = ""

        # Discover live servers asynchronously
        servers = []
        selected_server = None
        active = False
        active_custom = False
        loading = True
        back_button = pygame.Rect(screen_width * 0.05, screen_height * 0.8, screen_width * 0.2, screen_height * 0.08)
        join_button = pygame.Rect(screen_width * 0.55, screen_height * 0.75, screen_width * 0.3, screen_height * 0.08)
        add_server_button = pygame.Rect(screen_width * 0.55, screen_height * 0.65, screen_width * 0.3, screen_height * 0.08)

        # Lock for managing server list thread
        lock = threading.Lock()

        # Start the asynchronous server discovery
        discoverThread: threading.Thread = threading.Thread(target=discover_servers_async, args=(servers, lock), daemon=True).start()

        # Main loop
        while running:
            screen.fill(background_color)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint(event.pos):
                        current_scene = MainMenu(screen)
                        return
                    elif input_box.collidepoint(event.pos):
                        active = True
                        active_custom = False
                    elif custom_server_box.collidepoint(event.pos):
                        active_custom = True
                        active = False
                    else:
                        active = False
                        active_custom = False

                    # Handle server selection
                    for i, server in enumerate(servers):
                        server_rect = pygame.Rect(screen_width * 0.05, screen_height * (0.2 + i * 0.1), screen_width * 0.4, screen_height * 0.08)
                        if server_rect.collidepoint(event.pos):
                            selected_server = server

                    # Handle join button click
                    if join_button.collidepoint(event.pos) and selected_server:
                        serverIp = str.split(selected_server, "\n")[1]
                        newClient.username = username
                        newClient.connectToServer(ip=serverIp)
                        current_scene = Gameplay(screen)
                        return

                    # Handle custom server addition
                    if add_server_button.collidepoint(event.pos) and is_valid_ip(custom_server):
                        servers.append(f"Custom Server\n{custom_server}")
                        custom_server = ""  # Clear the input after adding the server

                elif event.type == pygame.KEYDOWN:
                    if active:
                        if event.key == pygame.K_RETURN:
                            active = False
                        elif event.key == pygame.K_BACKSPACE:
                            username = username[:-1]
                        else:
                            username += event.unicode
                    elif active_custom:
                        if event.key == pygame.K_RETURN:
                            active_custom = False
                        elif event.key == pygame.K_BACKSPACE:
                            custom_server = custom_server[:-1]
                        else:
                            custom_server += event.unicode

            # Draw live server list
            title_text = title_font.render("Available Servers", True, text_color)
            screen.blit(title_text, (screen_width * 0.05, screen_height * 0.1))

            with lock:
                for i, server in enumerate(servers):
                    server_rect = pygame.Rect(screen_width * 0.05, screen_height * (0.2 + i * 0.1), screen_width * 0.4, screen_height * 0.08)
                    pygame.draw.rect(screen, button_hover_color if selected_server == server else button_color, server_rect)
                    serverName = str.split(server, "\n")[0]
                    server_text = font.render(serverName, True, text_color)
                    screen.blit(server_text, (server_rect.x + 10, server_rect.y + 10))

            # Draw the join button
            if selected_server:
                pygame.draw.rect(screen, button_color, join_button)
            else:
                pygame.draw.rect(screen, disabled_color, join_button)

            # Draw username input
            username_label = font.render("Enter Username:", True, text_color)
            screen.blit(username_label, (screen_width * 0.55, screen_height * 0.35))

            # Draw input box for username
            pygame.draw.rect(screen, input_box_color, input_box, 2 if active else 1)
            username_surface = font.render(username, True, text_color)
            screen.blit(username_surface, (input_box.x + 10, input_box.y + 10))

            # Draw input box for custom server
            custom_server_label = font.render("Custom Server IP:", True, text_color)
            screen.blit(custom_server_label, (screen_width * 0.55, screen_height * 0.5))
            pygame.draw.rect(screen, input_box_color, custom_server_box, 2 if active_custom else 1)
            custom_server_surface = font.render(custom_server, True, text_color)
            screen.blit(custom_server_surface, (custom_server_box.x + 10, custom_server_box.y + 10))

            # Draw add server button
            if is_valid_ip(custom_server):
                pygame.draw.rect(screen, button_color, add_server_button)
            else:
                pygame.draw.rect(screen, disabled_color, add_server_button)
            add_server_text = font.render("Add Custom Server", True, text_color)
            screen.blit(add_server_text, add_server_button.move((add_server_button.width - add_server_text.get_width()) // 2, (add_server_button.height - add_server_text.get_height()) // 2))

            # Draw join and back buttons
            join_text = font.render("Join", True, text_color)
            screen.blit(join_text, join_button.move((join_button.width - join_text.get_width()) // 2, (join_button.height - join_text.get_height()) // 2))

            pygame.draw.rect(screen, button_color, back_button)
            back_text = font.render("Back", True, text_color)
            screen.blit(back_text, back_button.move((back_button.width - back_text.get_width()) // 2, (back_button.height - back_text.get_height()) // 2))

            # Update the display
            pygame.display.flip()

class MainMenu(Scene):
    def __init__(self, screen):
        super().__init__(screen)

    def handle_click(self, position):
        pass
        
    def render(self):
        global current_scene

        background_color = (30, 30, 30)
        title_color = (255, 255, 255)
        button_color = (50, 150, 255)
        button_hover_color = (70, 170, 255)
        text_color = (255, 255, 255)

        # Set up fonts
        title_font = pygame.font.Font(None, int(self.screen_height * 0.1))  # Title font size relative to screen height
        server_select_font = pygame.font.Font(None, int(self.screen_height * 0.05))  # Button font size relative to screen height

        # Set up title and button text
        title_text = title_font.render(GAME_NAME, True, title_color)
        server_select_text = server_select_font.render("Join a Server", True, text_color)

        # Calculate title position (centered near the top)
        title_rect = title_text.get_rect(center=(self.screen_width / 2, self.screen_height * 0.2))

        # Calculate button position (centered on screen)
        server_select_width, server_select_height = self.screen_width * 0.3, self.screen_height * 0.1  # Button size relative to screen
        server_select_rect = pygame.Rect(
            (self.screen_width / 2 - server_select_width / 2, self.screen_height / 2 - server_select_height / 2),
            (server_select_width, server_select_height)
        )

        screen.fill(background_color)

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if server_select_rect.collidepoint(event.pos):
                    ## Switch to the correct scene
                    current_scene = ServerSelect(screen)
                    return

        # Draw title
        screen.blit(title_text, title_rect)

        # Draw button (change color if hovered)
        mouse_pos = pygame.mouse.get_pos()
        if server_select_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, button_hover_color, server_select_rect)
        else:
            pygame.draw.rect(screen, button_color, server_select_rect)

        # Draw button text (centered on button)
        button_text_rect = server_select_text.get_rect(center=server_select_rect.center)
        screen.blit(server_select_text, button_text_rect)

        # Update the display
        pygame.display.flip()
        
current_scene = MainMenu(screen)

while running:
    current_scene.update()

newClient.disconnectFromServer()
pygame.quit()