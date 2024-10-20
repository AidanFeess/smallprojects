import logging.handlers
import socket, threading, logging
import struct, json
import pygame

from GameConstants import *

class NetworkServer():
    """
    A network server class that creates and hosts a new network server
    that manages client connections, and serves data to clients while alive.

    Args:
        gameServer (GameServer): A game server that holds game data like server name and world positions.
        host (str): A host IP address, defaults to local (127.0.0.1), common alternative is 0.0.0.0 for public.
        port (int): The desired port, defaults to 44200.
    """
    def __init__(self, gameServer: 'GameServer', host: str = "127.0.0.1", port: int = 44200):
        ## Declare the instance
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.shutdown_event = threading.Event()  # Create an event to signal server shutdown
        self.gameServer = gameServer
        self.live_clients = []
        self.all_client_data = {} # super hack way to do this, its 3 am

        # The 'entry message' sent to every client when they join the server.
        self.entryMessage = self.serialize_server_data(
            ServerJoinPacket(
                servername=gameServer.serverName,
                serverip=gameServer.serverIp,
                serverport=gameServer.serverPort
            )
        )

        # Set up log file
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
        self.udp_broadcast_socket.bind(('', port))  # Bind to the same port for discovery

        # Start the client-handling thread
        self.clientThread = threading.Thread(target=self.startClientHandling, name="client-thread", daemon=True)
        self.clientThread.start()

        try:
            self.logger.info(f"Server started on {socket.gethostbyname(socket.gethostname())}:{self.gameServer.serverPort}")
            while not self.shutdown_event.is_set():  # Main server loop checks shutdown event
                self.check_for_discovery_request() # also using it to check for discovery requests
                self.shutdown_event.wait(1)  # Wait for 1 second, then re-check if shutdown is requested

        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested via KeyboardInterrupt")

        finally:
            self.shutdown()

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
        while not self.shutdown_event.is_set():  # Check for server shutdown in the client-handling thread
            try:
                self.serverSocket.settimeout(1)  # Add a timeout to avoid blocking indefinitely
                clientSock, clientAddr = self.serverSocket.accept()
                threading.Thread(target=self.handleClient, args=(clientSock, clientAddr), daemon=True).start() # sub thread for each connected client
            except socket.timeout:
                continue  # Timeout occurred, check again if shutdown_event is set

    def handleClient(self, clientSock: socket.socket, clientAddr):
        """
        Handles communication with a connected client.
        
        Args:
            clientSock (socket): The socket object for the connected client.
            clientAddr (tuple): The client's address.
        """
        try:
            self.logger.info(f"Client {clientAddr} connected.")
            self.live_clients.append(clientAddr[0])

            # Give the client basic log-in information
            clientSock.sendall(self.entryMessage)

            while not self.shutdown_event.is_set():
                # Try to receive the message length (4 bytes)
                raw_length = self.recv_exact(clientSock, 4)
                if not raw_length:
                    break  # Client disconnected

                # Get the actual message length
                message_length = struct.unpack('!I', raw_length)[0]

                # Receive the actual message
                rawClientPacket = self.recv_exact(clientSock, message_length)
                if not rawClientPacket:
                    break  # Client disconnected

                # Deserialize the data
                clientPacket = self.deserialize_client_data(rawClientPacket)
                self.all_client_data[clientAddr[0]] = rawClientPacket
                combined_data = json.dumps({
                    addr: rawPacket.decode('utf-8') if rawPacket is not None and rawPacket != rawClientPacket else None 
                    for addr, rawPacket in self.all_client_data.items()
                }) + "\n"

                clientSock.sendall(combined_data.encode('utf-8'))


        except ConnectionResetError as e:
            self.logger.warning(f"Client {clientAddr} disconnected unexpectedly: {e}")
        except Exception as e:
            self.logger.exception(f"There was an error while handling a client: {e}")
        finally:
            self.cleanup_client(clientSock, clientAddr)

    def recv_exact(self, sock: socket.socket, length: int) -> bytes:
        """
        Receives the exact number of bytes from the socket.

        Args:
            sock (socket): The socket to receive from.
            length (int): The number of bytes to receive.

        Returns:
            bytes: The received data, or None if the connection is closed.
        """
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
        """
        Cleans up the client connection after disconnection or error.
        
        Args:
            clientSock (socket): The socket object for the client.
            clientAddr (tuple): The client's address.
        """
        del(self.all_client_data[clientAddr[0]]) # remove entry in client data
        self.live_clients.remove(clientAddr[0]) # remove the live client
        clientSock.close()
        self.logger.info(f"Client {clientAddr} disconnected and cleaned up.")

    def serialize_server_data(self, packet: ServerJoinPacket) -> bytes:
        # Convert the dataclass to a dictionary for JSON serialization
        data_dict = {
            "servername": packet.servername,
            "serverip": packet.serverip,
            "serverport": packet.serverport
        }
        return json.dumps(data_dict).encode('utf-8')

    def deserialize_client_data(self, data: bytes) -> ClientPacket:
        data_dict = json.loads(data.decode('utf-8')) # opposite of serializing
        position = Position(**data_dict['position'])
        gameData = GameData(**data_dict['gameData'])
        return ClientPacket(username=data_dict['username'], position=position, gameData=gameData)

    def shutdown(self):
        """Gracefully shuts down the server."""
        self.logger.info("Shutting down the server...")
        self.shutdown_event.set()  # Signal all threads to stop
        self.clientThread.join()  # Ensure the client-handling thread stops
        self.serverSocket.close()  # Close the server socket
        self.udp_broadcast_socket.close()
        self.logger.info("Server shutdown complete.")

class GameServer():
    """
    A gameserver that allows for the creation, deletion, and editing of objects
    as well as the visualization of the game world if needed.
    """

    def __init__(self, serverName = "OfficialServer", serverIp = "127.0.0.1", serverPort = 44200, isVisual = False):
        self.serverName = serverName
        self.serverIp = serverIp
        self.serverPort = serverPort
        self.isVisual = isVisual

    def start(self):
        self.networkServer = NetworkServer(self, self.serverIp, self.serverPort)
    
    def visualizeGameData():
        pass

# Create and start the server
newServer = GameServer(serverName="Test Server", serverIp="0.0.0.0")
newServer.start()
