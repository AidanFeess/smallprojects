import pygame
import random
import base64
import os
import socket
import threading

from Entities import *
from GameConstants import *
from PlayerData import *

# Server Configuration
HOST = '127.0.0.1'  # Localhost for testing purposes
PORT = 5555        # Port to listen on

# List to keep track of active connections
active_connections = []

# Lock for thread-safe operations on active connections
connections_lock = threading.Lock()

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(GAME_NAME)

# Game variables
player_speed = 5
projectile_speed = 7

reload_time = 500  # Milliseconds between each shot
max_projectiles = 3  # Max projectiles at a time
lives = 3

current_score = 0
p_data = PlayerData()

# Fonts
font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 72)

# Button setup
button_width = 200
button_height = 50
restart_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 50, button_width, button_height)
exit_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 150, button_width, button_height)

# Helper Functions

def draw_text(text, font, color, surface, x, y):
    """Draws text at a given location"""
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.center = (x, y)
    surface.blit(text_obj, text_rect)

def reset_game():
    """Resets the game state"""
    global player, projectiles, current_score, lives, game_over, reference_object, world_offset_x, world_offset_y
    player = spawn_entity(Player, 0, 0)  # Player starts at world center
    projectiles = []
    current_score = 0
    lives = 3
    game_over = False
    reference_object = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 50, 50)  # Reset reference object position
    world_offset_x = 0
    world_offset_y = 0

def start_screen():
    """Displays the start screen with high score, start, and exit buttons."""
    start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2, button_width, button_height)
    exit_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 100, button_width, button_height)

    screen.fill(BLACK)
    draw_text(f'{GAME_NAME}', large_font, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150)
    draw_text(f'High Score: {p_data.get_data("high_score")}', font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)

    pygame.draw.rect(screen, GREEN, start_button_rect)
    draw_text('START', font, BLACK, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 25)

    pygame.draw.rect(screen, BLUE, exit_button_rect)
    draw_text('EXIT', font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 125)

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if start_button_rect.collidepoint(mouse_pos):
                    return  # Start the game
                if exit_button_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    quit()

# Generalized function to spawn any entity at a given position
def spawn_entity(entity_class, x, y):
    """Creates and returns an instance of the specified entity class"""
    return entity_class(x, y)

def handle_client(conn, addr):
    """Handles the client connection."""
    print(f"[NEW CONNECTION] {addr} connected.")
    
    with connections_lock:
        active_connections.append((conn, addr))

    connected = True
    while connected:
        try:
            message = conn.recv(1024).decode('utf-8')
            if not message:
                break
            # For now, just log the received message
            print(f"[{addr}] {message}")
        except ConnectionResetError:
            break

    # Remove the connection when client disconnects
    with connections_lock:
        active_connections.remove((conn, addr))
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

# Game setup
# Start screen
start_screen()

# Player and Spider setup
player = spawn_entity(Player, 0, 0)  # Player starts at world center

# Reference object setup
reference_object = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 50, 50)

# Game variables
projectiles = []
last_shot_time = 0  # Track when the player last shot
game_over = False
running = True
clock = pygame.time.Clock()

# World offset variables
world_offset_x = 0
world_offset_y = 0

# Main game loop
while running:
    screen.fill(BLACK)

    if not game_over:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
        keys = pygame.key.get_pressed()
        old_player_position = player.rect.topleft
        player.handle_input(keys)
        player.update()
        new_player_position = player.rect.topleft

        # Calculate the player's change in position
        delta_x = new_player_position[0] - old_player_position[0]
        delta_y = new_player_position[1] - old_player_position[1]

        # Update the world offset by the change in player's position
        world_offset_x -= delta_x
        world_offset_y -= delta_y

        # Draw reference object (stationary in world coordinates)
        reference_object_moved = reference_object.move(world_offset_x, world_offset_y)
        pygame.draw.rect(screen, RED, reference_object_moved)

        # Draw player at the center of the screen
        player.rect.topleft = (SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2, SCREEN_HEIGHT // 2 - PLAYER_HEIGHT // 2)
        player.draw(screen)
        
        score_text = font.render(f"Score: {current_score}", True, WHITE)
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        screen.blit(score_text, (10, SCREEN_HEIGHT - 30))
        screen.blit(lives_text, (10, SCREEN_HEIGHT - 60))

    else:
        # Game over screen
        draw_text('GAME OVER', large_font, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
        draw_text(f'Your Score: {current_score}', font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)
        draw_text(f'High Score: {p_data.get_data("high_score")}', font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Draw the restart button
        pygame.draw.rect(screen, GREEN, restart_button_rect)
        draw_text('RESTART', font, BLACK, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 75)

        # Draw the exit button
        pygame.draw.rect(screen, BLUE, exit_button_rect)
        draw_text('EXIT', font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 175)

        # Handle restart and exit button clicks
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if restart_button_rect.collidepoint(mouse_pos):
                    reset_game()
                if exit_button_rect.collidepoint(mouse_pos):
                    running = False

    # Refresh the screen
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

p_data.update_high_score(current_score)

# Quit pygame
pygame.quit()
