import socket, struct
import threading, json, time
import pygame

from GameConstants import *

class NetworkClient:
    """
    A client class that handles client connections to the server,
    stores and receives data from the server. Meant to only be
    used indirectly through the GameClient
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
            print(f"Connected to server at {self.host}:{self.port}")

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
    A client class meant to be used directly for a player. Holds important
    data and functions that allow for logging into servers and manipulating
    the player's presence in the game world.

    Args:
        gameData (dict): A dictionary of game data like health, upgrades, etc.
        username (str): The user's username
        position (Vector3): The player's current Vector2 position
    """
    def __init__(self, gameData: GameData, username: str = "Guest", position: Position = (0, 0)):
        self.gameData = gameData
        self.username = username
        self.position = position

    def connectToServer(self, ip: str = "127.0.0.1", port: int = 44200):
        self.networkClient = NetworkClient(self, ip, port)

newClient = GameClient(GameData(HP=100), "User1", pygame.Vector2(0, 0))
newClient.connectToServer()

