import socket, struct
import threading, json, time
import pygame

from GameConstants import *

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
            self.serverInfo = self.deserialize_server_data(self.connection.recv(1024))

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
                self.connect_to_server()

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
newClient = GameClient(GameData(HP=100), "User2", pygame.Vector2(0, 0))
newClient.connectToServer()

## Pygame setup
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True
dt = 0

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

newClient.disconnectFromServer()
pygame.quit()