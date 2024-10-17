import socket
import threading
import pygame

# Server Configuration
HOST = '127.0.0.1'  # Change this to the server's IP if running on a different machine
PORT = 5555

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Basic Client")

# Fonts
FONT = pygame.font.SysFont(None, 36)

# Player Configuration
PLAYER_WIDTH, PLAYER_HEIGHT = 30, 30
player_position = [400, 300]
player_velocity = [0, 0]

# Socket Configuration
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# World objects list to store data received from server
world_objects = []
# Other players list to store data received from server
other_players = []

# Function to handle server communication
def receive_data():
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            # Parse received data
            player_data, world_objects_data, other_players_data = data.split('|')
            
            # Parse world objects
            world_objects.clear()
            world_objects_split = world_objects_data.split(';')
            for obj_str in world_objects_split:
                if obj_str:
                    obj_info = obj_str.split(',')
                    if len(obj_info) == 5:
                        world_objects.append({'type': obj_info[0], 'rect': pygame.Rect(int(obj_info[1]), int(obj_info[2]), int(obj_info[3]), int(obj_info[4]))})
            
            # Parse other players
            other_players.clear()
            other_players_split = other_players_data.split(';')
            for player_str in other_players_split:
                if player_str:
                    player_info = player_str.split(',')
                    if len(player_info) == 3:
                        other_players.append({'name': player_info[0], 'position': (int(player_info[1]), int(player_info[2]))})
        except (ConnectionResetError, ValueError):
            break

# Start a thread to receive data from the server
receive_thread = threading.Thread(target=receive_data, daemon=True)
receive_thread.start()

# Game variables
running = True
clock = pygame.time.Clock()

# Main game loop
while running:
    screen.fill((0, 0, 0))

    # Event handling
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        player_velocity[0] = -5
    elif keys[pygame.K_d]:
        player_velocity[0] = 5
    else:
        player_velocity[0] = 0

    if keys[pygame.K_w]:
        player_velocity[1] = -5
    elif keys[pygame.K_s]:
        player_velocity[1] = 5
    else:
        player_velocity[1] = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            print("[QUIT] Quit event received, stopping game loop.")

    # Update player position
    player_position[0] += player_velocity[0]
    player_position[1] += player_velocity[1]

    # Send player position to the server
    client_socket.send(f"{player_velocity[0]},{player_velocity[1]}".encode('utf-8'))

    # Draw world objects
    for obj in world_objects:
        obj_rect_moved = obj['rect'].move(-player_position[0] + 400, -player_position[1] + 300)
        pygame.draw.rect(screen, (255, 0, 0), obj_rect_moved)

    # Draw other players
    for player in other_players:
        if player['name'] != "You":
            other_player_rect = pygame.Rect(player['position'][0] - player_position[0] + 400, player['position'][1] - player_position[1] + 300, PLAYER_WIDTH, PLAYER_HEIGHT)
            pygame.draw.rect(screen, (0, 255, 0), other_player_rect)
            text_surface = FONT.render(player['name'], True, (255, 255, 255))
            screen.blit(text_surface, (other_player_rect.x, other_player_rect.y - 20))

    # Draw player
    player_rect = pygame.Rect(400, 300, PLAYER_WIDTH, PLAYER_HEIGHT)
    pygame.draw.rect(screen, (0, 0, 255), player_rect)
    text_surface = FONT.render("You", True, (255, 255, 255))
    screen.blit(text_surface, (player_rect.x, player_rect.y - 20))

    # Refresh the screen
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

# Quit pygame
pygame.quit()
print("[QUIT] Pygame terminated.")

# Close socket connection
client_socket.close()
