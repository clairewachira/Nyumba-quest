import pygame
import math
import random
import time
import pygame.mixer

pygame.mixer.init()
bg_music = pygame.mixer.Sound('audio/bg.mp3')
item_pickup_sound = pygame.mixer.Sound('audio/item.wav')
treasure_pickup_sound = pygame.mixer.Sound('audio/win.wav')
button_sound = pygame.mixer.Sound('audio/button.mp3')

# Screen dimensions
SCENE_WIDTH = 600
SCENE_HEIGHT = 600
TOTAL_WIDTH = 1000

# OTHER GAME CONSTANTS
TIME_BETWEEN_AI_SPAWNS = 10
TIME_BETWEEN_HEALTH_SPAWNS = 20
HEALTH_DECREASE_RATE = 0.08
FORWARD_SPEED = 1.5
BACKWARD_SPEED = -1.5
ROTATE_SPEED = 0.05
SPEED_MULTIPLIER = 0.5
FPS = 60
AI_SPEED = 0.8
HEALTH_MAX = 100
HEALTH_MIN = 0
HEALTH_PICKUP_AMOUNT = 20
WALL_COLLISION_THRESHOLD = 10
SPAWN_THRESHOLD_PADDING = 80
AI_DISTANCE_THRESHOLD = 15
FOV = 60

# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (100, 255, 100)
PURPLE = (50, 0, 50)
RED = (255, 0, 0)
DARK_GREY = (200, 200, 200)
BRIGHT_GREY = (100, 100, 100)

# SPRITE SIZES
PLAYER_SIZE = (50, 50)
AI_CHARACTER_SIZE = (70, 70)
TREASURE_SIZE = (40, 40)
HEALTH_SIZE = (60, 40)


class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def set(self, x, y):
        self.x = x
        self.y = y

    def normalize(self):
        mag = math.sqrt(self.x**2 + self.y**2)
        if mag > 0:
            self.x /= mag
            self.y /= mag

    def copy(self):
        return Vector(self.x, self.y)


class Boundary:
    def __init__(self, x1, y1, x2, y2, wall_type='normal'):
        self.a = Vector(x1, y1)
        self.b = Vector(x2, y2)
        self.wall_type = wall_type

    def draw(self, screen):
        color_map = {
            'normal': WHITE,
            'window': BLUE,
        }
        pygame.draw.line(screen, color_map.get(self.wall_type, WHITE),
                         (self.a.x, self.a.y),
                         (self.b.x, self.b.y), 3)
class AICharacter:
    def __init__(self, x, y):
        self.pos = Vector(x, y)
        self.speed = AI_SPEED

    def move_towards(self, player_pos):
        # Calculate direction vector towards player
        dir_x = player_pos.x - self.pos.x
        dir_y = player_pos.y - self.pos.y
        mag = math.sqrt(dir_x**2 + dir_y**2)
        if mag > 0:
            dir_x /= mag
            dir_y /= mag

        # Move towards the player
        self.pos.x += dir_x * self.speed
        self.pos.y += dir_y * self.speed

    def draw(self, screen):
        ai_sprite = pygame.image.load('images/enemy.png').convert_alpha()
        player_sprite = pygame.transform.scale(ai_sprite, AI_CHARACTER_SIZE)
        screen.blit(player_sprite, (int(self.pos.x - 16), int(self.pos.y - 16)))



class Item:
    def __init__(self, x, y, item_type):
        self.pos = Vector(x, y)
        self.type = item_type
        self.collected = False

    def draw(self, screen):
        treasure_sprite = pygame.image.load('images/treasure.png').convert_alpha()
        health_sprite = pygame.image.load('images/health.png').convert_alpha()
        treasure_sprite = pygame.transform.scale(treasure_sprite, TREASURE_SIZE)
        health_sprite = pygame.transform.scale(health_sprite, HEALTH_SIZE)
        if not self.collected:
            color_map = {
                'treasure': treasure_sprite,
                'health': health_sprite
            }

            screen.blit(color_map.get(self.type, (200, 200, 200)),
                        (int(self.pos.x - 16), int(self.pos.y - 16)))

class Ray:
    def __init__(self, pos, angle):
        self.pos = pos
        self.dir = Vector(math.cos(angle), math.sin(angle))

    def set_angle(self, angle):
        self.dir.set(math.cos(angle), math.sin(angle))

    def look_at(self, x, y):
        self.dir.x = x - self.pos.x
        self.dir.y = y - self.pos.y
        self.dir.normalize()

    def draw(self, screen):
        end_x = self.pos.x + self.dir.x * 10
        end_y = self.pos.y + self.dir.y * 10
        pygame.draw.line(screen, (100, 100, 100),
                         (self.pos.x, self.pos.y),
                         (end_x, end_y))

    def cast(self, wall):
        x1, y1 = wall.a.x, wall.a.y
        x2, y2 = wall.b.x, wall.b.y
        x3, y3 = self.pos.x, self.pos.y
        x4 = x3 + self.dir.x
        y4 = y3 + self.dir.y

        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if den == 0:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if 0 <= t <= 1 and u > 0:
            pt = Vector()
            pt.x = x1 + t * (x2 - x1)
            pt.y = y1 + t * (y2 - y1)
            return pt
        return None

class Player:
    def __init__(self, scene_width, scene_height):
        self.pos = Vector(scene_width // 2, scene_height // 2)
        self.scene_width = scene_width
        self.scene_height = scene_height

        self.rays = []
        self.fov = math.radians(FOV)
        self.heading = 0

        self.health = HEALTH_MAX
        self.inventory = []

        # Create rays for FOV
        for a in range(int(math.degrees(self.fov))):
            ray = Ray(self.pos, math.radians(a))
            self.rays.append(ray)

    def rotate(self, angle):
        self.heading += angle
        for i, ray in enumerate(self.rays):
            ray_angle = math.radians(i) + self.heading
            ray.set_angle(ray_angle)
    def move(self, walls, amount):
        # Calculate movement vector
        forward = Vector(math.cos(self.heading), math.sin(self.heading))
        forward.normalize()
        movement = forward.copy()
        movement.x *= amount * SPEED_MULTIPLIER
        movement.y *= amount * SPEED_MULTIPLIER

        # Proposed new position
        new_x = self.pos.x + movement.x
        new_y = self.pos.y + movement.y

        # Check for wall collisions
        collision = False
        for wall in walls:
            dist = point_to_line_distance(new_x, new_y, wall.a.x, wall.a.y, wall.b.x, wall.b.y)
            if dist < WALL_COLLISION_THRESHOLD:  # Threshold for collision
                collision = True
                break

        # Move if no collision and within bounds
        if not collision and (0 <= new_x < self.scene_width) and (0 <= new_y < self.scene_height):
            self.pos.x = new_x
            self.pos.y = new_y
        else:
            pass


        # Update ray positions
        for ray in self.rays:
            ray.pos = self.pos.copy()

    def collect_item(self, items):
        for item in items:
            if not item.collected:
                dist = math.sqrt((self.pos.x - item.pos.x)**2 + (self.pos.y - item.pos.y)**2)
                if dist < 15:  # Item pickup range
                    item.collected = True
                    self.inventory.append(item.type)

                    # Special item effects
                    if item.type == 'health':
                        item_pickup_sound.play()
                        self.health = min(HEALTH_MAX, self.health + HEALTH_PICKUP_AMOUNT)

                    if item.type == 'treasure':
                        treasure_pickup_sound.play()

    def draw(self, screen):
        player_sprite = pygame.image.load('images/player_sprite.png').convert_alpha()
        player_sprite = pygame.transform.scale(player_sprite, PLAYER_SIZE)
        screen.blit(player_sprite, (int(self.pos.x - 16), int(self.pos.y - 16)))
        for ray in self.rays:
            ray.draw(screen)

    def look(self, walls):
        scene = []
        for ray in self.rays:
            closest = float('inf')
            closest_type = None
            for wall in walls:
                pt = ray.cast(wall)
                if pt:
                    dist = math.sqrt((pt.x - ray.pos.x)**2 + (pt.y - ray.pos.y)**2)
                    if dist < closest:
                        closest = dist
                        closest_type = 'wall'

            scene.append((closest, closest_type))
        return scene

def point_to_line_distance(px, py, ax, ay, bx, by):
    # Calculate the distance from point (px, py) to line segment (ax, ay) -> (bx, by)
    line_len = math.sqrt((bx - ax)**2 + (by - ay)**2)
    if line_len == 0:  # The line segment is a single point
        return math.sqrt((px - ax)**2 + (py - ay)**2)

    # Project point onto the line segment
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / (line_len**2)))
    proj_x = ax + t * (bx - ax)
    proj_y = ay + t * (by - ay)

    # Distance from the point to the projected point
    return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)


def spawn_health_item(items, scene_width, scene_height):
    # Randomly spawn a health item
    x = random.randint(SPAWN_THRESHOLD_PADDING, scene_width - SPAWN_THRESHOLD_PADDING)
    y = random.randint(SPAWN_THRESHOLD_PADDING, scene_height - SPAWN_THRESHOLD_PADDING)
    items.append(Item(x, y, 'health'))

def create_house_layout(scene_width, scene_height):
    walls = [
        # Outer walls
        Boundary(50, 50, scene_width - 50, 50),  # Top wall
        Boundary(scene_width - 50, 50, scene_width - 50, scene_height - 50),  # Right wall
        Boundary(scene_width - 50, scene_height - 50, 50, scene_height - 50),  # Bottom wall
        Boundary(50, scene_height - 50, 50, 50),  # Left wall

        # Living Room Walls
        Boundary(150, 150, 250, 150),  # Top wall, gap for doorway
        Boundary(350, 150, 350, 250),  # Right wall, gap for doorway
        Boundary(350, 350, 250, 350),  # Bottom wall, gap for doorway
        Boundary(150, 350, 150, 250),  # Left wall, gap for doorway

        # Kitchen Walls
        Boundary(350, 150, 450, 150),  # Top wall, gap for doorway
        Boundary(500, 150, 500, 250),  # Right wall, gap for doorway
        Boundary(500, 350, 450, 350),  # Bottom wall, gap for doorway

        # Bedroom Walls
        Boundary(150, 350, 150, 400),  # Left wall, gap for doorway
        Boundary(150, 500, 250, 500),  # Bottom wall, gap for doorway
        Boundary(350, 500, 350, 400),  # Right wall, gap for doorway

        # Hallway
        Boundary(350, 250, 350, 350),  # Center vertical hallway
    ]

    # Windows
    walls.extend([
        Boundary(50, 200, 100, 200, 'window'),
        Boundary(50, 400, 100, 400, 'window'),
        Boundary(scene_width - 100, 200, scene_width - 50, 200, 'window'),
        Boundary(scene_width - 100, 400, scene_width - 50, 400, 'window'),
    ])

    # Place items within the house
    items = [
        Item(random.randint(SPAWN_THRESHOLD_PADDING, SCENE_WIDTH - SPAWN_THRESHOLD_PADDING), random.randint(SPAWN_THRESHOLD_PADDING, SCENE_HEIGHT - SPAWN_THRESHOLD_PADDING), 'treasure'),
        Item(random.randint(SPAWN_THRESHOLD_PADDING, SCENE_WIDTH - SPAWN_THRESHOLD_PADDING), random.randint(SPAWN_THRESHOLD_PADDING, SCENE_HEIGHT - SPAWN_THRESHOLD_PADDING), 'health'),
    ]

    return walls, items

def menu(screen, font, options, title=None):
    running = True
    selected_option = None

    while running:
        screen.fill(PURPLE)

        if title:
            title_text = font.render(title, True, WHITE)
            title_rect = title_text.get_rect(center=(screen.get_width() // 2, 50))
            screen.blit(title_text, title_rect)

        # Draw menu buttons
        button_width, button_height = 200, 50
        y_offset = 150
        for i, option in enumerate(options):
            btn_x = screen.get_width() // 2 - button_width // 2
            btn_y = y_offset + i * (button_height + 20)  # Add spacing between buttons
            is_hovered = pygame.Rect(btn_x, btn_y, button_width, button_height).collidepoint(pygame.mouse.get_pos())
            draw_button(screen, option, font, btn_x, btn_y, button_width, button_height, is_hovered)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                for i, option in enumerate(options):
                    btn_x = screen.get_width() // 2 - button_width // 2
                    btn_y = y_offset + i * (button_height + 20)
                    rect = pygame.Rect(btn_x, btn_y, button_width, button_height)
                    if rect.collidepoint(mouse_x, mouse_y):
                        button_sound.play()
                        selected_option = option
                        running = False

        pygame.display.flip()

    return selected_option

def draw_button(screen, text, font, x, y, width, height, is_hovered):
    # Set the button color based on hover state
    color = DARK_GREY if is_hovered else BRIGHT_GREY
    pygame.draw.rect(screen, color, (x, y, width, height))

    # Draw the text centered inside the button rectangle to allow clicking
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)


def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((TOTAL_WIDTH, SCENE_HEIGHT))
    pygame.display.set_caption('Nyumba Quest')
    font = pygame.font.Font(None, 36)

    clock = pygame.time.Clock()

    # Create house layout
    walls, items = create_house_layout(SCENE_WIDTH, SCENE_HEIGHT)

    menu_choice = menu(screen, font, ["Start Game", "Exit"], "Welcome to Nyumba Quest!")
    if menu_choice == "Exit":
        pygame.quit()
        return

    player = Player(SCENE_WIDTH, SCENE_HEIGHT)
    ai_characters = []  # List of AI enemies
    ai_spawn_timer = time.time()
    health_spawn_timer = time.time()

    running = True
    victory = False

    while running:
        bg_music.play(loops=-1)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Pause menu during game
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pause_choice = menu(screen, font, ["Resume", "Restart", "Exit"], "Game Paused")
            if pause_choice == "Exit":
                running = False
            elif pause_choice == "Restart":
                main()
                return

        if not victory and player.health > 0:
            # Handle continuous key presses
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player.rotate(-ROTATE_SPEED)
            if keys[pygame.K_RIGHT]:
                player.rotate(ROTATE_SPEED)
            if keys[pygame.K_UP]:
                player.move(walls, FORWARD_SPEED)
            if keys[pygame.K_DOWN]:
                player.move(walls, BACKWARD_SPEED)

            # Spawn AI characters periodically
            if time.time() - ai_spawn_timer > TIME_BETWEEN_AI_SPAWNS:
                x = random.randint(SPAWN_THRESHOLD_PADDING, SCENE_WIDTH - SPAWN_THRESHOLD_PADDING)
                y = random.randint(SPAWN_THRESHOLD_PADDING, SCENE_HEIGHT - SPAWN_THRESHOLD_PADDING)
                ai_characters.append(AICharacter(x, y))
                ai_spawn_timer = time.time()

            # Spawn health items periodically
            if time.time() - health_spawn_timer > TIME_BETWEEN_HEALTH_SPAWNS:  # Health spawns every 20 seconds
                spawn_health_item(items, SCENE_WIDTH, SCENE_HEIGHT)
                health_spawn_timer = time.time()

            # Move AI characters and check for collision with player
            for ai in ai_characters:
                ai.move_towards(player.pos)
                dist = math.sqrt((ai.pos.x - player.pos.x)**2 + (ai.pos.y - player.pos.y)**2)

                if dist < AI_DISTANCE_THRESHOLD:  # AI attacks player if too close
                    player.health -= HEALTH_DECREASE_RATE

            # Collect items
            player.collect_item(items)

            # Check for victory
            for item in items:
                if item.type == 'treasure' and item.collected:
                    victory = True

        # Draw scene
        screen.fill(BLACK)

        # Draw walls
        for wall in walls:
            wall.draw(screen)

        # Draw items
        for item in items:
            if not item.collected:
                item.draw(screen)

        # Draw AI characters
        for ai in ai_characters:
            ai.draw(screen)

        # Draw player
        player.draw(screen)

        # Render 3D-like scene
        scene = player.look(walls)
        slice_width = SCENE_WIDTH // len(player.rays)

        for i, (distance, object_type) in enumerate(scene):
            # Map distance to brightness
            sq_dist = distance * distance
            max_sq_dist = SCENE_WIDTH * SCENE_WIDTH
            brightness = int(pygame.math.lerp(255, 0, sq_dist / max_sq_dist))

            # Map height of wall slice
            height = int(pygame.math.lerp(SCENE_HEIGHT, 0, distance / SCENE_WIDTH))

            rect_x = SCENE_WIDTH + i * slice_width
            rect_y = (SCENE_HEIGHT - height) // 2

            pygame.draw.rect(screen, (brightness, brightness, brightness),
                             (rect_x, rect_y, slice_width + 1, height))

        # Draw UI
        inventory_text = font.render(f'Inventory: {", ".join(player.inventory)}', True, WHITE)
        health_text = font.render(f'Health: {int(player.health)}', True, RED)
        screen.blit(inventory_text, (SCENE_WIDTH + 10, 50))
        screen.blit(health_text, (SCENE_WIDTH + 10, 100))

        # Victory or Game Over
        if victory:
            victory_text = font.render('Victory! You found the treasure!', True, GREEN)
            screen.blit(victory_text, (SCENE_WIDTH + 10, 150))
        elif player.health <= HEALTH_MIN:
            game_over_text = font.render('Game Over! You died!', True, RED)
            screen.blit(game_over_text, (SCENE_WIDTH + 10, 150))

        if victory or player.health <= HEALTH_MIN:
            result_text = "You Win!" if victory else "Game Over!"
            result_choice = menu(screen, font, ["Restart", "Exit"], result_text)
            if result_choice == "Restart":
                main()
                return
            elif result_choice == "Exit":
                running = False


        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
