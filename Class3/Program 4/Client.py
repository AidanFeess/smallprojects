import socket, struct
import threading, json, time
import pygame

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
                data = self.connection.recv(1024).decode('utf-8')

                if not data:
                    break  # Server closed the connection

                buffer += data

                # Process all complete messages in the buffer
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)  # Split at the first newline
                    
                    # Deserialize the JSON string into a Python dictionary
                    self.gameClient.allClients = json.loads(message)  

                time.sleep(0.1)  # send data every 100 ms

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
            self.serverInfo = self.deserialize_server_data(serverData)

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

    def deserialize_server_data(self, data: bytes):
        """
        Deserializes the server info packet from the server.
        """
        data_dict = json.loads(data.decode('utf-8'))
        return ServerJoinPacket(
            servername=data_dict["servername"],
            serverip=data_dict["serverip"],
            serverport=data_dict["serverport"]
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
        self.worldObjects = [ # TODO: I think a better idea is to make everything a sprite no matter what, even the player.
            WorldObject(Position(0, 0), RED, 50, 50, ObjectType(isRect=True, isCircle=False, isSprite=False)),
            WorldObject(Position(0, 0), BLUE, 30, 30, ObjectType(isRect=False, isCircle=True, isSprite=False)),
        ]
        self.allClients = {} # just some filler for future
        self.velocity = 5

    def connectToServer(self, ip: str = "127.0.0.1", port: int = 44200):
        self.networkClient = NetworkClient(self, ip, port)  # Example placeholder

    def disconnectFromServer(self):
        self.networkClient.disconnect()  # Example placeholder

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
        pygame.draw.rect(screen, BLUE, pygame.Rect(SCREEN_WIDTH//2 - PLAYER_WIDTH//2, SCREEN_HEIGHT//2 - PLAYER_HEIGHT//2, PLAYER_WIDTH, PLAYER_HEIGHT))

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

    def renderOtherClients(self, screen):
        for client in self.allClients:
            # Convert string to dictionary
            client = json.loads(self.allClients[client])
            if client['username'] == self.username:
                continue  # Skip the current client (player)

            # Get the client position and convert to screen coordinates
            clientPosition = client['position']
            screenPosition = CalculateScreenPosition(pygame.Vector2(clientPosition['x'], clientPosition['y']), self.position)

            # Draw the other client's representation (e.g., a rectangle)
            pygame.draw.rect(screen, GREEN, (
                screenPosition.x - PLAYER_WIDTH // 2,  # X coordinate
                screenPosition.y - PLAYER_HEIGHT // 2,  # Y coordinate
                PLAYER_WIDTH, PLAYER_HEIGHT  # Width and Height of the client rectangle
            ))
newClient = GameClient(GameData(HP=100), "User1", pygame.Vector2(0, 0))

## Pygame setup
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True
dt = 0

## Pygame Functions
def display_game(screen):
    global running

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        newClient.handleMovement(keys)
        screen.fill(WHITE)

        newClient.drawWorldObjects(screen)
        newClient.draw(screen) # Draw the client on top (probably needs some more advanced stuff later for layering)
        newClient.renderOtherClients(screen)

        pygame.display.flip()    
        dt = clock.tick(60) / 1000

def display_server_select(screen):
    global running

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
    username = ""

    # Discover live servers asynchronously
    servers = []
    selected_server = None
    active = False
    loading = True
    back_button = pygame.Rect(screen_width * 0.05, screen_height * 0.8, screen_width * 0.2, screen_height * 0.08)
    join_button = pygame.Rect(screen_width * 0.55, screen_height * 0.7, screen_width * 0.3, screen_height * 0.08)
    
    # Lock for managing server list thread
    lock = threading.Lock()
    
    # Start the asynchronous server discovery
    threading.Thread(target=discover_servers_async, args=(servers, lock), daemon=True).start()

    # Main loop
    while running:
        screen.fill(background_color)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return  # Go back to the main menu
                elif input_box.collidepoint(event.pos):
                    active = True
                else:
                    active = False
                # Handle server selection
                for i, server in enumerate(servers):
                    server_rect = pygame.Rect(screen_width * 0.05, screen_height * (0.2 + i * 0.1), screen_width * 0.4, screen_height * 0.08)
                    if server_rect.collidepoint(event.pos):
                        selected_server = server
                if join_button.collidepoint(event.pos) and selected_server:
                    serverIp = str.split(server, "\n")[1]
                    newClient.connectToServer(ip=serverIp)
                    display_game(screen)
                    return  # You would trigger the join server action here
            elif event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    username += event.unicode

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

        # create the join button
        

        # Show loading message if no servers yet
        if not servers:
            loading_text = font.render("Searching for servers...", True, text_color)
            screen.blit(loading_text, (screen_width * 0.05, screen_height * 0.2))
            
            # also show the join button as grey if there are no servers
            pygame.draw.rect(screen, disabled_color, join_button)
        else:
            pygame.draw.rect(screen, button_color, join_button)

        # Draw username input
        username_label = font.render("Enter Username:", True, text_color)
        screen.blit(username_label, (screen_width * 0.55, screen_height * 0.35))

        # Draw input box
        pygame.draw.rect(screen, input_box_color, input_box, 2 if active else 1)
        username_surface = font.render(username, True, text_color)
        screen.blit(username_surface, (input_box.x + 10, input_box.y + 10))

        ## Draw buttons
        # the join button is a bit different so we draw the button earlier
        join_text = font.render("Join", True, text_color)
        screen.blit(join_text, join_button.move((join_button.width - join_text.get_width()) // 2, (join_button.height - join_text.get_height()) // 2))

        pygame.draw.rect(screen, button_color, back_button)
        back_text = font.render("Back", True, text_color)
        screen.blit(back_text, back_button.move((back_button.width - back_text.get_width()) // 2, (back_button.height - back_text.get_height()) // 2))

        # Update the display
        pygame.display.flip()

def display_menu(screen):
    # Initialize pygame font
    global running
    pygame.font.init()

    # Set up colors
    background_color = (30, 30, 30)
    title_color = (255, 255, 255)
    button_color = (50, 150, 255)
    button_hover_color = (70, 170, 255)
    text_color = (255, 255, 255)

    # Get screen dimensions
    screen_width, screen_height = screen.get_size()

    # Set up fonts
    title_font = pygame.font.Font(None, int(screen_height * 0.1))  # Title font size relative to screen height
    button_font = pygame.font.Font(None, int(screen_height * 0.05))  # Button font size relative to screen height

    # Set up title and button text
    title_text = title_font.render(GAME_NAME, True, title_color)
    button_text = button_font.render("Join a Server", True, text_color)

    # Calculate title position (centered near the top)
    title_rect = title_text.get_rect(center=(screen_width / 2, screen_height * 0.2))

    # Calculate button position (centered on screen)
    button_width, button_height = screen_width * 0.3, screen_height * 0.1  # Button size relative to screen
    button_rect = pygame.Rect(
        (screen_width / 2 - button_width / 2, screen_height / 2 - button_height / 2),
        (button_width, button_height)
    )

    # Main menu loop
    while running:
        screen.fill(background_color)

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    display_server_select(screen)
                    return

        # Draw title
        screen.blit(title_text, title_rect)

        # Draw button (change color if hovered)
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, button_hover_color, button_rect)
        else:
            pygame.draw.rect(screen, button_color, button_rect)

        # Draw button text (centered on button)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, button_text_rect)

        # Update the display
        pygame.display.flip()

display_menu(screen) # display the initial start menu.

newClient.disconnectFromServer()
pygame.quit()