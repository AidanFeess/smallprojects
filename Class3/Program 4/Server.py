import logging.handlers
import socket, threading, logging
import struct, json
import pygame, time
from random import randint
from typing import List
from GameConstants import *
import secrets

# Generate a unique token
unique_id = secrets.token_hex(8)

class NetworkServer():
    """
    A network server class that creates and hosts a new network server
    that manages client connections and serves data to clients while alive.
    """

    def __init__(self, gameServer: 'GameServer', host: str = "127.0.0.1", port: int = 44200):
        # Declare the instance
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.shutdown_event = threading.Event()  # Create an event to signal server shutdown
        self.gameServer = gameServer
        self.live_clients = []
        self.all_client_data = {}
        self.last_update_time = pygame.time.get_ticks()  # Initialize to track delta time (dt)

        # The 'entry message' sent to every client when they join the server.
        self.entryMessage = self.serialize_server_join_data(
            ServerJoinPacket(
                servername=gameServer.serverName,
                serverip=gameServer.serverIp,
                serverport=gameServer.serverPort
            )
        )

        # Set up logging
        self.logfilePath = SERVERDATADIR / f"Server.log"
        with open(self.logfilePath, 'a'):  # Create the log file
            pass

        handlers = [logging.handlers.RotatingFileHandler(
            filename=self.logfilePath,
            mode='w',
            maxBytes=512000,
            backupCount=0
        )]
        self.BasicConfig = logging.basicConfig(
            handlers=handlers,
            level=0,
            format='%(levelname)s %(asctime)s | %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )

        self.logger = logging.getLogger("server")
        self.logger.info(f"Server initialized")

        # Bind and listen
        self.serverSocket.bind((host, port))
        self.serverSocket.listen()

        # Create a UDP socket for server discovery
        self.udp_broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_broadcast_socket.bind(('', port))

        # Start the client-handling thread
        self.clientThread = threading.Thread(target=self.startClientHandling, name="client-thread", daemon=True)
        self.clientThread.start()

        self.updateThread = threading.Thread(target=self.update_game_state, name="update-thread", daemon=True)
        self.updateThread.start()

        try:
            self.logger.info(f"Server started on {socket.gethostbyname(socket.gethostname())}:{self.gameServer.serverPort}")
            while not self.shutdown_event.is_set():  # Main server loop checks shutdown event
                self.check_for_discovery_request()
                self.shutdown_event.wait(1)

        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested via KeyboardInterrupt")

        finally:
            self.shutdown()

    def update_game_state(self):
        """
        Continuously updates the game state in the background.
        """
        while not self.shutdown_event.is_set():  # Run while the server is active
            time.sleep(0.01667)  # Update the game state every 16.77 ms (60 FPS)

            current_time = time.time()  # Get current time in seconds
            dt = min(current_time - self.last_update_time, 2)  # Calculate delta time in seconds, capped to prevent large jumps
            self.last_update_time = current_time

            # Get a list of client positions from self.all_client_data
            client_positions = []
            for data in self.all_client_data.values():
                client_data = json.loads(data.decode('utf-8'))
                x = client_data['position']['x']
                y = client_data['position']['y']
                client_positions.append(pygame.Vector2(x, y))

            # Update enemies using the current client positions and dt
            self.gameServer.update_enemies(client_positions, dt)
            
    def check_for_discovery_request(self):
        """Check for UDP broadcast discovery requests and respond to them."""
        self.udp_broadcast_socket.settimeout(0.1)  # Non-blocking or short timeout
        try:
            message, client_address = self.udp_broadcast_socket.recvfrom(1024)
            if message.decode('utf-8') == "DISCOVER_SERVERS":
                response_message = f"{self.gameServer.serverName}\n{socket.gethostbyname(socket.gethostname())}"
                self.udp_broadcast_socket.sendto(response_message.encode('utf-8'), client_address)
        except socket.timeout:
            pass  # No message received, continue

    def startClientHandling(self):
        while not self.shutdown_event.is_set():
            try:
                self.serverSocket.settimeout(1)  # Add a timeout to avoid blocking indefinitely
                clientSock, clientAddr = self.serverSocket.accept()
                if clientAddr[0] in self.live_clients:  # Not accepting duplicate clients
                    clientSock.sendall("[CLOSECONNECTION]".encode('utf-8'))
                    continue
                threading.Thread(target=self.handleClient, args=(clientSock, clientAddr), daemon=True).start()
            except socket.timeout:
                continue  # Timeout occurred, check again if shutdown_event is set

    def handleClient(self, clientSock: socket.socket, clientAddr):
        """
        Handles communication with a connected client.
        """
        try:
            self.logger.info(f"Client {clientAddr} connected.")
            self.live_clients.append(clientAddr[0])

            # Send entry information
            clientSock.sendall(self.entryMessage)

            while not self.shutdown_event.is_set():
                raw_length = self.recv_exact(clientSock, 4)
                if not raw_length:
                    break  # Client disconnected
                
                # Deserialize the received packet
                message_length = struct.unpack('!I', raw_length)[0]
                rawClientPacket = self.recv_exact(clientSock, message_length)
                if not rawClientPacket:
                    break  # Client disconnected

                data_dict = json.loads(rawClientPacket.decode('utf-8'))

                # Check if the packet contains a damage header
                if "header" in data_dict and data_dict["header"] == "DAMAGE_TO_WHO":
                    # Process the damage packet
                    damage_list = data_dict["damage_data"]
                    for damage_entry in damage_list:
                        enemy_id = damage_entry["id"]
                        damage = damage_entry["damage"]

                        # Apply damage to the corresponding enemy
                        if enemy_id in self.gameServer.enemies:
                            self.gameServer.enemies[enemy_id].health -= damage
                            if self.gameServer.enemies[enemy_id].health <= 0:
                                self.gameServer.enemies[enemy_id].die()

                # Otherwise, treat it as a normal client packet
                clientPacket = self.deserialize_client_data(rawClientPacket)

                # Update the client data with the newly received packet
                self.all_client_data[clientAddr[0]] = rawClientPacket
                enemy_data = {}
                for id, enemy in self.gameServer.enemies.items():
                    enemy_data[id] = {
                        "position": {"x": enemy.position.x, "y": enemy.position.y},
                        "health": enemy.health,
                        "animation_frame": enemy.current_frame_index,
                        "current_animation": enemy.current_animation,
                        "is_alive": enemy.is_alive
                    }

                # Prepare the updated data to broadcast to other clients
                combined_data = json.dumps({
                    addr: rawPacket.decode('utf-8') if rawPacket is not None else None
                    for addr, rawPacket in self.all_client_data.items()
                })

                serverPacket = self.serialize_server_data(
                    ServerPacket(
                        terrain=self.gameServer.terrain,
                        clients_data=combined_data,
                        enemy_data=enemy_data  # Include the enemy data in the packet
                    )
                )

                clientSock.sendall(serverPacket)

        except ConnectionResetError as e:
            self.logger.warning(f"Client {clientAddr} disconnected unexpectedly: {e}")
        except Exception as e:
            self.logger.exception(f"Error while handling a client: {e}")
        finally:
            self.cleanup_client(clientSock, clientAddr)

    def recv_exact(self, sock: socket.socket, length: int) -> bytes:
        """Receives the exact number of bytes from the socket."""
        data = b''
        try:
            while len(data) < length:
                packet = sock.recv(length - len(data))
                if not packet:
                    return None  # Connection closed by the client
                data += packet
            return data
        except (ConnectionResetError, ConnectionAbortedError):
            return None  # Client disconnected unexpectedly

    def cleanup_client(self, clientSock: socket.socket, clientAddr):
        """Cleans up the client connection after disconnection or error."""
        try:
            del self.all_client_data[clientAddr[0]]  # Remove entry in client data
            self.live_clients.remove(clientAddr[0])  # Remove the live client
        except (Exception, Exception) as e:
            self.logger.error(f"Failed to remove client from data: {e}")
            self.live_clients.remove(clientAddr[0])
        clientSock.close()
        self.logger.info(f"Client {clientAddr} disconnected and cleaned up.")

    def serialize_server_join_data(self, packet: ServerJoinPacket) -> bytes:
        data_dict = {
            "servername": packet.servername,
            "serverip": packet.serverip,
            "serverport": packet.serverport
        }
        return json.dumps(data_dict).encode('utf-8')

    def serialize_server_data(self, packet: ServerPacket) -> bytes:
        """
        Serializes the server packet to JSON format.
        """
        data_dict = {
            "terrain": packet.terrain,
            "clients_data": packet.clients_data,
            "enemy_data": packet.enemy_data  # Include the enemy data for serialization
        }
        return json.dumps(data_dict).encode('utf-8')

    def deserialize_client_data(self, data: bytes) -> ClientPacket:
        """
        Deserializes the client packet from the received bytes.
        """
        data_dict = json.loads(data.decode('utf-8'))

        # Handle deserialization of current_weapon
        weapon_data = data_dict['gameData'].get('current_weapon')
        current_weapon = None
        if weapon_data:
            current_weapon = Weapon(
                name=weapon_data["name"],
                range=weapon_data["range"],
                damage=weapon_data["damage"]
            )

        position = Position(**data_dict['position'])
        gameData = GameData(
            HP=data_dict['gameData']['HP'],
            facing_right=data_dict['gameData']['facing_right'],
            current_animation=data_dict['gameData']['current_animation'],
            current_frame_index=data_dict['gameData']['current_frame_index'],
            last_frame_time=data_dict['gameData']['last_frame_time'],
            player_scale=data_dict['gameData']['player_scale'],
            velocity=data_dict['gameData']['velocity'],
            velocity_y=data_dict['gameData']['velocity_y'],
            grounded=data_dict['gameData']['grounded'],
            movement_disabled=data_dict['gameData']['movement_disabled'],
            animation_in_progress=data_dict['gameData']['animation_in_progress'],
            current_weapon=current_weapon
        )

        return ClientPacket(username=data_dict['username'], position=position, gameData=gameData)

    def shutdown(self):
        """Gracefully shuts down the server."""
        self.logger.info("Shutting down the server...")
        self.shutdown_event.set()  # Signal all threads to stop
        self.clientThread.join()  # Ensure the client-handling thread stops
        self.updateThread.join()
        self.serverSocket.close()  # Close the server socket
        self.udp_broadcast_socket.close()
        self.logger.info("Server shutdown complete.")

class GameServer():
    """
    A gameserver that allows for the creation, deletion, and editing of objects.
    """

    def __init__(self, serverName="OfficialServer", serverIp="127.0.0.1", serverPort=44200):
        self.serverName = serverName
        self.serverIp = serverIp
        self.serverPort = serverPort
        self.terrain = None
        self.enemies = {}  # A list of all spawned enemies
        self.enemy_data = {}  # Data about enemies to be sent to clients

    def start(self):
        self.terrain = self.generateCityscape(8000)
        self.spawn_enemy(pygame.Vector2(0, 0))
        self.spawn_enemy(pygame.Vector2(3000, 0))

        self.networkServer = NetworkServer(self, self.serverIp, self.serverPort)

    def spawn_enemy(self, position: pygame.Vector2):
        """
        Spawns a new enemy and adds it to the server's enemy list.
        """
        new_enemy = Enemy(position, is_server=True)  # Indicate that this is server-side
        self.enemies[secrets.token_hex(8)] = new_enemy

    def update_enemies(self, client_positions: List[pygame.Vector2], dt: float):
        """
        Updates each enemy in the game, making them chase the nearest client.
        
        Args:
            client_positions (List[pygame.Vector2]): A list of client positions.
            dt (float): Delta time for frame-independent movement.
        """
        self.enemy_data = {}  # Clear the previous frame's data
        
        for id, enemy in self.enemies.items():
            enemy: Enemy
            if enemy.is_alive:
                # Update enemy logic (chasing nearest client, moving)
                enemy.update(clients_positions=client_positions, terrain=self.terrain, dt=dt)

                # Store updated data for this enemy to send to clients
                self.enemy_data[id] = {
                    "position": {"x": enemy.position.x, "y": enemy.position.y},
                    "health": enemy.health,
                    "animation_frame": enemy.current_frame_index,
                    "current_animation": enemy.current_animation,  # Include current animation state
                    "is_alive": enemy.is_alive
                }

    def generateCityscape(self, width, building_width=500, min_height=350, max_height=700, space_between=100) -> List[List[Tuple[int, int]]]:
        """
        Generates 2D cityscape terrain resembling buildings as separate polygons.
        
        Explanation:
        - Generates flat square-like "roof tops" at different heights and includes building walls.
        - Buildings are spaced horizontally, and their heights are randomized between min_height and max_height.
        - The result is a list of lists, where each inner list represents the points for a single building.
        
        Args:
            width (int): The total width of the cityscape.
            building_width (int): The width of each building.
            min_height (int): The minimum height of the buildings.
            max_height (int): The maximum height of the buildings.
            space_between (int): The space between buildings.
        
        Returns:
            List[List[Tuple[int, int]]]: A list of buildings, each represented as a list of four points.
        """
        buildings = []
        current_x = -width // 2

        while current_x < width // 2:
            building_height = randint(min_height, max_height)
            building = [
                (current_x, -building_height),
                (current_x + building_width, -building_height),
                (current_x + building_width, 3000),
                (current_x, 3000)
            ]
            buildings.append(building)
            current_x += building_width + space_between
        
        return buildings

# Create and start the server
newServer = GameServer(serverName="Test Server", serverIp="0.0.0.0")
newServer.start()
