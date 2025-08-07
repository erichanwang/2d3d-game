import pygame
import sys
import os
import random

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
GREY = (170, 170, 170)
LIGHT_GREY = (210, 210, 210)
HOVER_GREY = (190, 190, 190)
UI_PANEL_COLOR = (240, 240, 240)

# --- Physics ---
GRAVITY = 0.5
JUMP_STRENGTH = -11
COYOTE_TIME_FRAMES = 4 # Frames you can still jump after leaving a platform

# --- Game States ---
MENU = "menu"
LEVEL_EDITOR = "level_editor"
LEVEL_SELECT = "level_select"
PLAYING = "playing"

# --- UI Classes ---
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, radius=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.radius = radius
        self.is_hovered = False

    def draw(self, screen, font):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=self.radius)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return self.is_hovered and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

# --- Game Object Classes ---
class PushableObject:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.is_static = True

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

# --- Game State Classes ---
class Menu:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 50)
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 200, 300, 60, "Level Editor", GREY, HOVER_GREY),
            Button(SCREEN_WIDTH // 2 - 150, 300, 300, 60, "Play Random Level", GREY, HOVER_GREY),
            Button(SCREEN_WIDTH // 2 - 150, 400, 300, 60, "Play Saved Level", GREY, HOVER_GREY),
        ]

    def handle_events(self, events):
        for event in events:
            if self.buttons[0].is_clicked(event):
                self.game.change_state(LEVEL_EDITOR)
            elif self.buttons[1].is_clicked(event):
                self.game.start_playing(level_data=self.generate_random_level())
            elif self.buttons[2].is_clicked(event):
                self.game.change_state(LEVEL_SELECT)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)

    def draw(self, screen):
        screen.fill(WHITE)
        title_font = pygame.font.Font(None, 74)
        title_surf = title_font.render("2D/3D Game", True, BLACK)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surf, title_rect)
        for button in self.buttons:
            button.draw(screen, self.font)
            
    def generate_random_level(self):
        level_data = []
        # Generate 5 to 10 random platforms
        for _ in range(random.randint(5, 10)):
            w = random.randint(80, 200)
            h = 20
            x = random.randint(0, SCREEN_WIDTH - w)
            y = random.randint(100, SCREEN_HEIGHT - 100)
            level_data.append(f"platform,{x},{y},{w},{h}")
        # Generate 1 to 3 random pushable boxes
        for _ in range(random.randint(1, 3)):
            size = 40
            x = random.randint(0, SCREEN_WIDTH - size)
            y = random.randint(100, SCREEN_HEIGHT - 100 - size)
            level_data.append(f"pushable,{x},{y},{size},{size}")
        return level_data

class LevelSelect:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 40)
        self.buttons = []
        self.levels_dir = "levels"
        self.load_levels()
        self.back_button = Button(30, SCREEN_HEIGHT - 70, 150, 50, "Back", GREY, HOVER_GREY)

    def load_levels(self):
        if not os.path.exists(self.levels_dir):
            os.makedirs(self.levels_dir)
        
        level_files = [f for f in os.listdir(self.levels_dir) if f.endswith(".txt")]
        for i, filename in enumerate(level_files):
            y_pos = 100 + i * 60
            self.buttons.append(Button(SCREEN_WIDTH // 2 - 150, y_pos, 300, 50, filename[:-4], LIGHT_GREY, HOVER_GREY))

    def handle_events(self, events):
        for event in events:
            if self.back_button.is_clicked(event):
                self.game.change_state(MENU)
            for i, button in enumerate(self.buttons):
                if button.is_clicked(event):
                    level_path = os.path.join(self.levels_dir, f"{button.text}.txt")
                    with open(level_path, 'r') as f:
                        level_data = f.readlines()
                    self.game.start_playing(level_data=level_data)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        for button in self.buttons:
            button.check_hover(mouse_pos)

    def draw(self, screen):
        screen.fill(WHITE)
        title_font = pygame.font.Font(None, 74)
        title_surf = title_font.render("Select a Level", True, BLACK)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title_surf, title_rect)
        self.back_button.draw(screen, self.font)
        for button in self.buttons:
            button.draw(screen, self.font)

class LevelEditor:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 30)
        self.platforms = [
            pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20), # Ground
            pygame.Rect(0, 0, SCREEN_WIDTH, 20) # Roof
        ]
        self.pushable_objects = []
        
        self.selected_object_type = "platform"
        self.palette_buttons = [
            Button(10, 50, 150, 40, "Platform", RED, (255, 100, 100)),
            Button(10, 100, 150, 40, "Pushable Box", PURPLE, (200, 100, 200))
        ]
        self.save_button = Button(10, SCREEN_HEIGHT - 60, 150, 40, "Save Level", GREEN, (100, 255, 100))
        self.back_button = Button(10, SCREEN_HEIGHT - 110, 150, 40, "Back to Menu", GREY, HOVER_GREY)

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if self.back_button.is_clicked(event):
                self.game.change_state(MENU)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                is_on_ui = any(btn.rect.collidepoint(mouse_pos) for btn in self.palette_buttons) or \
                           self.save_button.rect.collidepoint(mouse_pos) or \
                           self.back_button.rect.collidepoint(mouse_pos)
                if is_on_ui:
                    if self.palette_buttons[0].is_clicked(event): self.selected_object_type = "platform"
                    elif self.palette_buttons[1].is_clicked(event): self.selected_object_type = "pushable"
                    elif self.save_button.is_clicked(event): self.save_level()
                else:
                    if event.button == 1: # Left click to place
                        if self.selected_object_type == "platform":
                            self.platforms.append(pygame.Rect(mouse_pos[0] - 50, mouse_pos[1] - 10, 100, 20))
                        elif self.selected_object_type == "pushable":
                            self.pushable_objects.append(PushableObject(mouse_pos[0] - 20, mouse_pos[1] - 20, 40, 40, PURPLE))
                    elif event.button == 3: # Right click to delete
                        self.platforms = [p for p in self.platforms if not p.collidepoint(mouse_pos) and p.height != 20]
                        self.pushable_objects = [o for o in self.pushable_objects if not o.rect.collidepoint(mouse_pos)]

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.palette_buttons: button.check_hover(mouse_pos)
        self.save_button.check_hover(mouse_pos)
        self.back_button.check_hover(mouse_pos)

    def draw(self, screen):
        screen.fill(WHITE)
        for plat in self.platforms: pygame.draw.rect(screen, RED, plat)
        for obj in self.pushable_objects: obj.draw(screen)

        ui_panel = pygame.Rect(0, 0, 170, SCREEN_HEIGHT)
        pygame.draw.rect(screen, UI_PANEL_COLOR, ui_panel)
        
        title_surf = self.font.render("Editor", True, BLACK)
        screen.blit(title_surf, (10, 10))
        
        for button in self.palette_buttons: button.draw(screen, self.font)
        self.save_button.draw(screen, self.font)
        self.back_button.draw(screen, self.font)

        selected_text = self.font.render(f"Selected:", True, BLACK)
        screen.blit(selected_text, (10, 160))
        if self.selected_object_type == "platform":
            pygame.draw.rect(screen, RED, (10, 190, 100, 20))
        else:
            pygame.draw.rect(screen, PURPLE, (10, 190, 40, 40))
        
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] > ui_panel.right:
            if self.selected_object_type == "platform":
                ghost_rect = pygame.Rect(mouse_pos[0] - 50, mouse_pos[1] - 10, 100, 20)
                pygame.draw.rect(screen, (255, 150, 150, 150), ghost_rect)
            elif self.selected_object_type == "pushable":
                ghost_rect = pygame.Rect(mouse_pos[0] - 20, mouse_pos[1] - 20, 40, 40)
                pygame.draw.rect(screen, (200, 150, 200, 150), ghost_rect)

    def save_level(self):
        if not os.path.exists("levels"): os.makedirs("levels")
        filename = input("Enter level name to save (e.g., my_level): ")
        if not filename:
            print("Save cancelled.")
            return
        filepath = os.path.join("levels", f"{filename}.txt")
        with open(filepath, "w") as f:
            for plat in self.platforms:
                if plat.height != 20: # Don't save ground/roof
                    f.write(f"platform,{plat.x},{plat.y},{plat.width},{plat.height}\n")
            for obj in self.pushable_objects:
                f.write(f"pushable,{obj.rect.x},{obj.rect.y},{obj.rect.width},{obj.rect.height}\n")
        print(f"Level saved to {filepath}")

class Playing:
    def __init__(self, game, level_data=None):
        self.game = game
        self.is_3d_mode = False
        self.player_rect = pygame.Rect(100, SCREEN_HEIGHT - 100, 40, 40)
        self.player_vel_y = 0
        self.on_ground = False
        self.coyote_timer = 0
        self.is_grabbing = False
        self.grabbed_obj = None
        
        self.platforms = [
            pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20), # Ground
            pygame.Rect(0, 0, SCREEN_WIDTH, 20) # Roof
        ]
        self.pushable_objects = []
        self.load_level(level_data)

    def load_level(self, level_data):
        if level_data is None: # Default level
            self.platforms.extend([pygame.Rect(200, 450, 150, 20), pygame.Rect(400, 350, 150, 20)])
            self.pushable_objects.append(PushableObject(500, SCREEN_HEIGHT - 70, 40, 40, PURPLE))
        else:
            for item in level_data:
                parts = item.strip().split(',')
                obj_type, x, y, w, h = parts[0], *[int(p) for p in parts[1:]]
                if obj_type == "platform": self.platforms.append(pygame.Rect(x, y, w, h))
                elif obj_type == "pushable": self.pushable_objects.append(PushableObject(x, y, w, h, PURPLE))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.game.change_state(MENU)
                if event.key == pygame.K_SPACE: self.toggle_mode()
                if event.key == pygame.K_UP and (self.on_ground or self.coyote_timer > 0) and not self.is_3d_mode:
                    self.player_vel_y = JUMP_STRENGTH
                    self.coyote_timer = 0

    def toggle_mode(self):
        self.is_3d_mode = not self.is_3d_mode
        for obj in self.pushable_objects: obj.is_static = not self.is_3d_mode
        if self.is_3d_mode: self.player_vel_y = 0
        if self.is_grabbing: self.is_grabbing = False; self.grabbed_obj = None

    def update(self):
        keys = pygame.key.get_pressed()
        self.is_grabbing = keys[pygame.K_LSHIFT] and self.is_3d_mode
        
        # --- Movement ---
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 5
        dy = 0
        if self.is_3d_mode:
            dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 5
        else:
            self.player_vel_y += GRAVITY
            dy = self.player_vel_y

        # --- Collision Detection ---
        self.player_rect.x += dx
        self.handle_collisions('horizontal', dx)
        
        self.player_rect.y += dy
        self.handle_collisions('vertical', dy)

        if self.on_ground: self.coyote_timer = COYOTE_TIME_FRAMES
        else: self.coyote_timer -= 1

    def handle_collisions(self, axis, movement):
        # Static collisions
        collidables = self.platforms + [obj.rect for obj in self.pushable_objects if obj.is_static]
        for plat in collidables:
            if self.player_rect.colliderect(plat):
                if axis == 'horizontal':
                    if movement > 0: self.player_rect.right = plat.left
                    if movement < 0: self.player_rect.left = plat.right
                elif axis == 'vertical':
                    if movement > 0:
                        self.player_rect.bottom = plat.top
                        self.on_ground = True
                        self.player_vel_y = 0
                    if movement < 0:
                        self.player_rect.top = plat.bottom
                        self.player_vel_y = 0
        
        # 3D mode dynamic collisions
        if self.is_3d_mode:
            for obj in self.pushable_objects:
                if self.player_rect.colliderect(obj.rect):
                    if self.is_grabbing:
                        # Move grabbed object with player
                        if axis == 'horizontal': obj.rect.x += movement
                        if axis == 'vertical': obj.rect.y += movement
                    else:
                        # Simple push
                        if axis == 'horizontal':
                            if movement > 0: self.player_rect.right = obj.rect.left
                            if movement < 0: self.player_rect.left = obj.rect.right
                        if axis == 'vertical':
                            if movement > 0: self.player_rect.bottom = obj.rect.top
                            if movement < 0: self.player_rect.top = obj.rect.bottom

    def draw(self, screen):
        screen.fill(WHITE)
        player_color = GREEN if self.is_3d_mode else BLUE
        pygame.draw.rect(screen, player_color, self.player_rect)

        for plat in self.platforms: pygame.draw.rect(screen, RED, plat)
        for obj in self.pushable_objects: obj.draw(screen)

        font = pygame.font.Font(None, 36)
        mode_text = f"Mode: {'3D (Grab)' if self.is_grabbing else '3D' if self.is_3d_mode else '2D'}"
        text_surface = font.render(mode_text, True, BLACK)
        screen.blit(text_surface, (10, 10))

# --- Main Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D/3D Game")
        self.clock = pygame.time.Clock()
        self.is_running = True
        
        self.states = {
            MENU: Menu(self),
            LEVEL_EDITOR: LevelEditor(self),
            LEVEL_SELECT: LevelSelect(self)
        }
        self.current_state_name = MENU
        self.current_state = self.states[self.current_state_name]

    def change_state(self, new_state_name):
        if new_state_name in self.states:
            self.current_state = self.states[new_state_name]
            self.current_state_name = new_state_name

    def start_playing(self, level_data=None):
        self.states[PLAYING] = Playing(self, level_data=level_data)
        self.change_state(PLAYING)

    def run(self):
        while self.is_running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.is_running = False
            
            self.current_state.handle_events(events)
            self.current_state.update()
            self.current_state.draw(self.screen)
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
