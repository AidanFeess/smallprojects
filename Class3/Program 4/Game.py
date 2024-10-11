import pygame
import random
import base64
import os

from Entities import *
from Constants import *
from PlayerData import *

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Spider Shooter')

# Game variables
player_speed = 5
spider_speed = 4
projectile_speed = 7

reload_time = 500  # Milliseconds between each shot
max_projectiles = 3  # Max projectiles at a time
lives = 3

current_score = 0
p_data = PlayerData()

# Resize images to desired size
player_width, player_height = 50, 50
spider_width, spider_height = 40, 40

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
    global player, spider, projectiles, current_score, lives, game_over
    player = spawn_entity(Player, (SCREEN_WIDTH // 2 - player_width // 2), (SCREEN_HEIGHT - player_height - 10))
    spider = spawn_entity(Spider, 0, random.randint(10, SCREEN_HEIGHT // 2))
    projectiles = []
    current_score = 0
    lives = 3
    game_over = False

def start_screen():
    """Displays the start screen with high score, start, and exit buttons."""
    start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2, button_width, button_height)
    exit_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, SCREEN_HEIGHT // 2 + 100, button_width, button_height)

    screen.fill(BLACK)
    draw_text('Spider Shooter', large_font, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150)
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

# Game setup
# Start screen
start_screen()

# Player and Spider setup
player = spawn_entity(Player, SCREEN_WIDTH // 2 - player_width // 2, SCREEN_HEIGHT - player_height - 10)
spider = spawn_entity(Spider, 0, random.randint(10, SCREEN_HEIGHT // 2))

# Game variables
projectiles = []
last_shot_time = 0  # Track when the player last shot
game_over = False
running = True
clock = pygame.time.Clock()

# Main game loop
while running:
    screen.fill(BLACK)

    if not game_over:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Key press handling
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.rect.left > 0:
            player.move(x_direction=-1)
        if keys[pygame.K_d] and player.rect.right < SCREEN_WIDTH:
            player.move(x_direction=1)

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