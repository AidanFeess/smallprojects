import socket
import threading
import pygame

# Server Configuration
HOST = '0.0.0.0'
PORT = 5555

# List to keep track of active connections and player data
active_connections = []
player_data = {}

# World objects list to store positions and other relevant data
world_objects = [{'type': 'reference', 'rect': pygame.Rect(400, 300, 50, 50)}]

def handle_client(conn, addr):
    """Handles the client connection."""
    print(f"[NEW CONNECTION] {addr} connected.")
    
    active_connections.append((conn, addr))
    player_data[addr] = {'position': (400, 300), 'name': f'Player_{len(active_connections)}'}

    connected = True
    while connected:
        try:
            message = conn.recv(1024).decode('utf-8')
            if not message:
                break
            # Parse the received message (expected format: vx,vy)
            velocity_x, velocity_y = map(float, message.split(','))
            
            # Update player position
            player = player_data[addr]
            new_position_x = player['position'][0] + velocity_x
            new_position_y = player['position'][1] + velocity_y
            player['position'] = (new_position_x, new_position_y)
            
            # Prepare player data to send to all clients
            players_data = ";".join([f"{data['name']},{data['position'][0]},{data['position'][1]}" for data in player_data.values()])
            
            # Send updated player position, world objects, and other players' data back to the client
            response_data = f"{new_position_x},{new_position_y}"
            world_objects_data = ";".join([f"{obj['type']},{obj['rect'].x},{obj['rect'].y},{obj['rect'].width},{obj['rect'].height}" for obj in world_objects])
            response_data = f"{response_data}|{world_objects_data}|{players_data}"
            conn.send(response_data.encode('utf-8'))
        except (ConnectionResetError, ValueError):
            break

    # Remove the connection when client disconnects
    active_connections.remove((conn, addr))
    del player_data[addr]
    conn.close()
    print(f"[DISCONNECT] {addr} disconnected.")

def start_server():
    """Starts the server and listens for new connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {len(active_connections)}")

# Start the server in a separate thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Basic Server Visualization")

# Fonts
FONT = pygame.font.SysFont(None, 36)

# Game variables
running = True
clock = pygame.time.Clock()

# Main game loop
while running:
    screen.fill((0, 0, 0))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            print("[QUIT] Quit event received, stopping game loop.")

    # Draw world objects
    for obj in world_objects:
        pygame.draw.rect(screen, (255, 0, 0), obj['rect'])

    # Draw players from player_data
    for addr, data in player_data.items():
        position = data['position']
        player_rect = pygame.Rect(position[0], position[1], 30, 30)
        pygame.draw.rect(screen, (0, 0, 255), player_rect)
        # Draw player name above the player
        text_surface = FONT.render(data['name'], True, (255, 255, 255))
        screen.blit(text_surface, (player_rect.x, player_rect.y - 20))

    # Refresh the screen
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

# Quit pygame
pygame.quit()
print("[QUIT] Pygame terminated.")
