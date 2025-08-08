import pygame
import sys
import os
import random
import math

# --- Constants ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FPS = 60
GRID_SIZE = 20

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0) # Platforms
GREEN = (0, 255, 0) # Player in 3D
BLUE = (0, 0, 255) # Player in 2D
PURPLE = (128, 0, 128) # Pushable
GREY = (170, 170, 170) # Ground/Roof
LIGHT_GREY = (210, 210, 210)
HOVER_GREY = (190, 190, 190)
UI_PANEL_COLOR = (240, 240, 240)
TRAMPOLINE_COLOR = (0, 150, 150)
WALL_3D_COLOR = (100, 100, 255)
WALL_3D_SHADOW_COLOR = (0, 0, 0, 100)
SLOPE_COLOR = (255, 165, 0)
GOAL_COLOR = (255, 255, 0, 150)
SPIKE_COLOR = (100, 100, 100)
CHECKPOINT_COLOR = (100, 255, 100, 150)
CHECKPOINT_ACTIVE_COLOR = (200, 255, 200, 200)

# --- Physics ---
GRAVITY = 0.5
JUMP_STRENGTH = -11
TRAMPOLINE_BOUNCE = -20
COYOTE_TIME_FRAMES = 4
Z_JUMP_HEIGHT = 10
Z_JUMP_DURATION = 30 # frames

# --- Game States ---
MENU, LEVEL_EDITOR, LEVEL_SELECT, PLAYING, PLAYING_INFINITE = "menu", "level_editor", "level_select", "playing", "playing_infinite"

# --- Camera ---
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
    def apply(self, entity):
        rect_to_move = entity.rect if hasattr(entity, 'rect') else entity
        return rect_to_move.move(self.camera.topleft)
    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)
    def update(self, target):
        x = -target.centerx + int(SCREEN_WIDTH / 2)
        x = min(0, x)
        self.camera.topleft = (x, 0)

# --- UI Classes ---
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, radius=10, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.radius = radius
        self.is_hovered = False
        self.text_color = text_color
    def draw(self, screen, font):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=self.radius)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    def is_clicked(self, event):
        return self.is_hovered and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

class TextInputBox:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = LIGHT_GREY
        self.text = ""
        self.font = font
        self.active = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 2)
        text_surface = self.font.render(self.text, True, BLACK)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        self.rect.w = max(200, text_surface.get_width() + 10)

# --- Game Object Classes ---
class GameObject:
    def __init__(self, x, y, w, h, color, obj_type="platform"):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.type = obj_type
    def draw(self, screen, camera):
        pygame.draw.rect(screen, self.color, camera.apply(self))

class PushableObject(GameObject):
    def __init__(self, x, y, w, h, color):
        super().__init__(x, y, w, h, color, obj_type="pushable")
        self.is_static = True

class Slope(GameObject):
    def __init__(self, x, y, w, h, color, left_top, right_top):
        super().__init__(x, y, w, h, color, obj_type="slope")
        self.left_top = left_top
        self.right_top = right_top
        self.poly = [
            (self.rect.left, self.rect.top + self.left_top),
            (self.rect.right, self.rect.top + self.right_top),
            (self.rect.right, self.rect.bottom),
            (self.rect.left, self.rect.bottom)
        ]
    def draw(self, screen, camera):
        poly_points = [(p[0] + camera.camera.x, p[1] + camera.camera.y) for p in self.poly]
        pygame.draw.polygon(screen, self.color, poly_points)
    def get_y_at_x(self, x):
        start_x, start_y = self.rect.left, self.rect.top + self.left_top
        end_x, end_y = self.rect.right, self.rect.top + self.right_top
        if start_x == end_x: return start_y
        return start_y + (end_y - start_y) * ((x - start_x) / (end_x - start_x))

# --- Game State Classes (Menu, LevelSelect) ---
class Menu:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 50)
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 200, 300, 60, "Level Editor", GREY, HOVER_GREY),
            Button(SCREEN_WIDTH // 2 - 150, 300, 300, 60, "Play Infinite", GREY, HOVER_GREY),
            Button(SCREEN_WIDTH // 2 - 150, 400, 300, 60, "Play Saved Level", GREY, HOVER_GREY),
        ]
    def handle_events(self, events):
        for event in events:
            if self.buttons[0].is_clicked(event): self.game.change_state(LEVEL_EDITOR)
            elif self.buttons[1].is_clicked(event): self.game.change_state(PLAYING_INFINITE)
            elif self.buttons[2].is_clicked(event): self.game.change_state(LEVEL_SELECT)
    def update(self):
        for button in self.buttons: button.check_hover(pygame.mouse.get_pos())
    def draw(self, screen):
        screen.fill(WHITE)
        title_font = pygame.font.Font(None, 74)
        title_surf = title_font.render("2D/3D Game", True, BLACK)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surf, title_rect)
        for button in self.buttons: button.draw(screen, self.font)

class LevelSelect(Menu):
    def __init__(self, game):
        super().__init__(game)
        self.level_buttons = []
        self.levels_dir = "levels"
        self.load_levels()
        self.back_button = Button(30, SCREEN_HEIGHT - 70, 150, 50, "Back", GREY, HOVER_GREY)
    def load_levels(self):
        if not os.path.exists(self.levels_dir): os.makedirs(self.levels_dir)
        level_files = [f for f in os.listdir(self.levels_dir) if f.endswith(".txt")]
        for i, filename in enumerate(level_files):
            y_pos = 100 + i * 70
            name = filename[:-4]
            play_button = Button(SCREEN_WIDTH // 2 - 210, y_pos, 200, 50, f"Play '{name}'", LIGHT_GREY, HOVER_GREY)
            edit_button = Button(SCREEN_WIDTH // 2 + 10, y_pos, 200, 50, f"Edit '{name}'", LIGHT_GREY, HOVER_GREY)
            self.level_buttons.append({'play': play_button, 'edit': edit_button, 'filename': filename})
    def handle_events(self, events):
        for event in events:
            if self.back_button.is_clicked(event): self.game.change_state(MENU)
            for btn_group in self.level_buttons:
                level_path = os.path.join(self.levels_dir, btn_group['filename'])
                with open(level_path, 'r') as f:
                    level_data = f.readlines()
                if btn_group['play'].is_clicked(event):
                    self.game.start_playing(level_data=level_data)
                if btn_group['edit'].is_clicked(event):
                    self.game.start_editing(level_data=level_data)
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        for btn_group in self.level_buttons:
            btn_group['play'].check_hover(mouse_pos)
            btn_group['edit'].check_hover(mouse_pos)
    def draw(self, screen):
        screen.fill(WHITE)
        title_font = pygame.font.Font(None, 74)
        title_surf = title_font.render("Select a Level", True, BLACK)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 50)))
        self.back_button.draw(screen, self.font)
        for btn_group in self.level_buttons:
            btn_group['play'].draw(screen, self.font)
            btn_group['edit'].draw(screen, self.font)

# --- Level Editor ---
class LevelEditor(LevelSelect):
    def __init__(self, game, level_data=None):
        super().__init__(game)
        self.objects = []
        if level_data is None:
            self.objects.append(GameObject(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH * 2, 20, GREY, "ground"))
        else:
            self.load_level_for_edit(level_data)
        self.selected_object_type = None
        self.snap_to_grid = True
        self.ui_width = 220
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera.camera.x = 0
        self.font = pygame.font.Font(None, 40)
        self.button_font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 36)

        self.palette_buttons = [
            # Player & Level Control
            Button(10, 60, 200, 35, "Start Point", (200, 255, 200), (150, 255, 150)),
            Button(10, 105, 200, 35, "End Goal", (255, 255, 200), (255, 255, 150)),
            Button(10, 150, 200, 35, "Checkpoint", (200,255,200), (150,255,150)),
            # Basic Blocks
            Button(10, 205, 95, 35, "Platform", RED, (255,150,150)),
            Button(115, 205, 95, 35, "V-Wall", WALL_3D_COLOR, (150,150,255), text_color=WHITE),
            Button(10, 250, 95, 35, "Slope Up", SLOPE_COLOR, (255,200,100)),
            Button(115, 250, 95, 35, "Slope Down", SLOPE_COLOR, (255,200,100)),
            # Interactive Objects
            Button(10, 305, 95, 35, "Pushable", PURPLE, (200,150,200), text_color=WHITE),
            Button(115, 305, 95, 35, "Trampoline", TRAMPOLINE_COLOR, (100,200,200)),
            Button(10, 350, 95, 35, "3D Wall", WALL_3D_COLOR, (150,150,255), text_color=WHITE),
            Button(115, 350, 95, 35, "Spike", SPIKE_COLOR, (150,150,150), text_color=WHITE),
            # Delete
            Button(10, 410, 200, 35, "DELETE", (255,100,100), (255,50,50), text_color=WHITE)
        ]
        self.snap_button = Button(10, SCREEN_HEIGHT - 150, 200, 40, "Snap: ON", (200, 255, 200), (150, 255, 150))
        self.save_button = Button(10, SCREEN_HEIGHT - 105, 200, 40, "Save Level", (200, 255, 200), (150, 255, 150))
        self.back_button = Button(10, SCREEN_HEIGHT - 60, 200, 40, "Back to Menu", (220, 220, 220), HOVER_GREY)
        self.text_input_box = None

    def load_level_for_edit(self, level_data):
        for item in level_data:
            parts = item.strip().split(',')
            obj_type, data = parts[0], [int(p) for p in parts[1:]]
            if obj_type == "start": self.objects.append(GameObject(data[0], data[1], 40, 50, GREEN, "start"))
            elif obj_type == "goal": self.objects.append(GameObject(*data, GOAL_COLOR, "goal"))
            elif obj_type == "platform": self.objects.append(GameObject(*data, RED, "platform"))
            elif obj_type == "pushable": self.objects.append(PushableObject(*data, PURPLE))
            elif obj_type == "trampoline": self.objects.append(GameObject(*data, TRAMPOLINE_COLOR, "trampoline"))
            elif obj_type == "wall_3d": self.objects.append(GameObject(*data, WALL_3D_COLOR, "wall_3d"))
            elif obj_type == "v_wall": self.objects.append(GameObject(*data, WALL_3D_COLOR, "v_wall"))
            elif obj_type == "slope": self.objects.append(Slope(data[0], data[1], data[2], data[3], SLOPE_COLOR, data[4], data[5]))
            elif obj_type == "spike": self.objects.append(GameObject(*data, SPIKE_COLOR, "spike"))
            elif obj_type == "checkpoint": self.objects.append(GameObject(*data, CHECKPOINT_COLOR, "checkpoint"))

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if self.text_input_box:
                filename = self.text_input_box.handle_event(event)
                if filename is not None:
                    self.save_level(filename)
                    self.text_input_box = None
                return

            if self.back_button.is_clicked(event): self.game.change_state(MENU)
            if self.snap_button.is_clicked(event):
                self.snap_to_grid = not self.snap_to_grid
                self.snap_button.text = f"Snap: {'ON' if self.snap_to_grid else 'OFF'}"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(self.palette_buttons):
                    if btn.is_clicked(event):
                        self.selected_object_type = ["start", "goal", "checkpoint", "platform", "v_wall", "slope_up", "slope_down", "pushable", "trampoline", "wall_3d", "spike", "delete"][i]
                        return
                if self.save_button.is_clicked(event):
                    self.prompt_for_filename()
                    return

                if mouse_pos[0] > self.ui_width:
                    world_pos = (mouse_pos[0] - self.camera.camera.x, mouse_pos[1])
                    if event.button == 1:
                        if self.selected_object_type == "delete": self.delete_object(world_pos)
                        else: self.place_object(world_pos)
                else: self.selected_object_type = None

    def place_object(self, pos):
        if self.selected_object_type is None: return
        x, y = pos
        if self.snap_to_grid:
            x = (x // GRID_SIZE) * GRID_SIZE
            y = (y // GRID_SIZE) * GRID_SIZE
        
        if self.selected_object_type == "start": self.objects = [o for o in self.objects if o.type != "start"]; self.objects.append(GameObject(x, y, 40, 50, GREEN, "start"))
        elif self.selected_object_type == "goal": self.objects = [o for o in self.objects if o.type != "goal"]; self.objects.append(GameObject(x, y, 80, 80, GOAL_COLOR, "goal"))
        elif self.selected_object_type == "platform": self.objects.append(GameObject(x, y, 100, 20, RED, "platform"))
        elif self.selected_object_type == "pushable": self.objects.append(PushableObject(x, y, 40, 40, PURPLE))
        elif self.selected_object_type == "trampoline": self.objects.append(GameObject(x, y, 80, 20, TRAMPOLINE_COLOR, "trampoline"))
        elif self.selected_object_type == "wall_3d": self.objects.append(GameObject(x, y, 20, 100, WALL_3D_COLOR, "wall_3d"))
        elif self.selected_object_type == "v_wall": self.objects.append(GameObject(x, y, 100, 20, WALL_3D_COLOR, "v_wall"))
        elif self.selected_object_type == "slope_up": self.objects.append(Slope(x, y, 100, 100, SLOPE_COLOR, 100, 0))
        elif self.selected_object_type == "slope_down": self.objects.append(Slope(x, y, 100, 100, SLOPE_COLOR, 0, 100))
        elif self.selected_object_type == "spike": self.objects.append(GameObject(x, y, 20, 20, SPIKE_COLOR, "spike"))
        elif self.selected_object_type == "checkpoint": self.objects.append(GameObject(x, y, 20, 60, CHECKPOINT_COLOR, "checkpoint"))

    def delete_object(self, pos):
        self.objects = [o for o in self.objects if not o.rect.collidepoint(pos)]

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.camera.camera.x += 10
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.camera.camera.x -= 10
        self.camera.camera.x = min(0, self.camera.camera.x)
        
        mouse_pos = pygame.mouse.get_pos()
        for button in self.palette_buttons: button.check_hover(mouse_pos)
        self.save_button.check_hover(mouse_pos)
        self.back_button.check_hover(mouse_pos)
        self.snap_button.check_hover(mouse_pos)

    def draw(self, screen):
        screen.fill(WHITE)
        self.draw_grid(screen)
        for obj in self.objects:
            if obj.type == "spike":
                pts = [(obj.rect.left, obj.rect.bottom), (obj.rect.centerx, obj.rect.top), (obj.rect.right, obj.rect.bottom)]
                cam_pts = [(p[0] + self.camera.camera.x, p[1] + self.camera.camera.y) for p in pts]
                pygame.draw.polygon(screen, obj.color, cam_pts)
            elif isinstance(obj, Slope): obj.draw(screen, self.camera)
            else: pygame.draw.rect(screen, obj.color, self.camera.apply(obj))
        self.draw_ghost(screen)
        ui_panel = pygame.Rect(0, 0, self.ui_width, SCREEN_HEIGHT)
        pygame.draw.rect(screen, UI_PANEL_COLOR, ui_panel)
        title_surf = self.title_font.render("Level Editor", True, BLACK)
        title_rect = title_surf.get_rect(center=(self.ui_width // 2, 30))
        screen.blit(title_surf, title_rect)
        for button in self.palette_buttons: button.draw(screen, self.button_font)
        self.snap_button.draw(screen, self.button_font)
        self.save_button.draw(screen, self.button_font)
        self.back_button.draw(screen, self.button_font)

        if self.text_input_box:
            self.text_input_box.draw(screen)

    def draw_grid(self, screen):
        if self.snap_to_grid:
            offset_x = self.camera.camera.x % GRID_SIZE
            for x in range(0, SCREEN_WIDTH + GRID_SIZE, GRID_SIZE): pygame.draw.line(screen, LIGHT_GREY, (x + offset_x, 0), (x + offset_x, SCREEN_HEIGHT))
            for y in range(0, SCREEN_HEIGHT, GRID_SIZE): pygame.draw.line(screen, LIGHT_GREY, (0, y), (SCREEN_WIDTH, y))

    def draw_ghost(self, screen):
        if self.selected_object_type is None: return
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] <= self.ui_width: return
        x, y = mouse_pos
        if self.snap_to_grid:
            x = (x // GRID_SIZE) * GRID_SIZE
            y = (y // GRID_SIZE) * GRID_SIZE
        
        ghost_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        ghost_surface.set_alpha(128)
        
        if self.selected_object_type == "platform": pygame.draw.rect(ghost_surface, RED, (0, 0, 100, 20)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "pushable": pygame.draw.rect(ghost_surface, PURPLE, (0, 0, 40, 40)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "trampoline": pygame.draw.rect(ghost_surface, TRAMPOLINE_COLOR, (0, 0, 80, 20)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "wall_3d": pygame.draw.rect(ghost_surface, WALL_3D_COLOR, (0, 0, 20, 100)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "slope_up": pygame.draw.polygon(ghost_surface, SLOPE_COLOR, [(0, 100), (100, 0), (100, 100)]); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "slope_down": pygame.draw.polygon(ghost_surface, SLOPE_COLOR, [(0, 0), (100, 100), (0, 100)]); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "start": pygame.draw.rect(ghost_surface, GREEN, (0, 0, 40, 50)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "goal": pygame.draw.rect(ghost_surface, GOAL_COLOR, (0, 0, 80, 80)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "v_wall": pygame.draw.rect(ghost_surface, WALL_3D_COLOR, (0, 0, 100, 20)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "checkpoint": pygame.draw.rect(ghost_surface, CHECKPOINT_COLOR, (0, 0, 20, 60)); screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "spike":
            pygame.draw.polygon(ghost_surface, SPIKE_COLOR, [(0, 20), (10, 0), (20, 20)])
            screen.blit(ghost_surface, (x, y))
        elif self.selected_object_type == "delete":
            pygame.draw.line(screen, RED, (x - 10, y - 10), (x + 10, y + 10), 3)
            pygame.draw.line(screen, RED, (x - 10, y + 10), (x + 10, y - 10), 3)

    def prompt_for_filename(self):
        self.text_input_box = TextInputBox(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 20, 300, 40, self.font)

    def save_level(self, filename):
        if not filename:
            print("Save cancelled.")
            return
        has_start = any(o.type == "start" for o in self.objects)
        has_goal = any(o.type == "goal" for o in self.objects)
        if not has_start or not has_goal:
            print("ERROR: Level must have a Start Point and an End Goal to be saved.")
            # Optionally, show this message on screen
            return
        if not os.path.exists("levels"): os.makedirs("levels")
        with open(os.path.join("levels", f"{filename}.txt"), "w") as f:
            for obj in self.objects:
                if isinstance(obj, Slope):
                    f.write(f"{obj.type},{obj.rect.x},{obj.rect.y},{obj.rect.width},{obj.rect.height},{obj.left_top},{obj.right_top}\n")
                else:
                    f.write(f"{obj.type},{obj.rect.x},{obj.rect.y},{obj.rect.width},{obj.rect.height}\n")
        print(f"Level saved to {filename}.txt")

# --- Playing State ---
class Playing:
    def __init__(self, game, level_data=None):
        self.game = game
        self.is_3d_mode = False
        self.player = pygame.Rect(100, SCREEN_HEIGHT - 100, 40, 50)
        self.player_vel_y = 0
        self.player_z = 0
        self.player_vel_z = 0
        self.on_ground = False
        self.coyote_timer = 0
        self.is_grabbing = False
        self.is_wall_sliding = False
        self.wall_slide_dir = None
        self.platforms, self.pushable_objects, self.trampolines, self.walls_3d, self.slopes, self.spikes, self.checkpoints, self.v_walls = [], [], [], [], [], [], [], []
        self.start_pos = (100, SCREEN_HEIGHT - 100)
        self.last_checkpoint = self.start_pos
        self.goal_rect = None
        self.level_data = level_data
        self.load_level(self.level_data)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

    def load_level(self, level_data):
        self.platforms = [pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH * 2, 20)]
        self.pushable_objects, self.trampolines, self.walls_3d, self.slopes, self.spikes, self.checkpoints, self.v_walls = [], [], [], [], [], [], []
        if level_data:
            for item in level_data:
                parts = item.strip().split(',')
                obj_type, data = parts[0], [int(p) for p in parts[1:]]
                if obj_type == "start": 
                    self.start_pos = (data[0], data[1])
                    self.player.topleft = self.start_pos
                    self.last_checkpoint = self.start_pos
                elif obj_type == "goal": self.goal_rect = pygame.Rect(*data)
                elif obj_type == "platform": self.platforms.append(pygame.Rect(*data))
                elif obj_type == "pushable": self.pushable_objects.append(PushableObject(*data, PURPLE))
                elif obj_type == "trampoline": self.trampolines.append(pygame.Rect(*data))
                elif obj_type == "wall_3d": self.walls_3d.append(pygame.Rect(*data))
                elif obj_type == "v_wall": self.v_walls.append(pygame.Rect(*data))
                elif obj_type == "slope": self.slopes.append(Slope(data[0], data[1], data[2], data[3], SLOPE_COLOR, data[4], data[5]))
                elif obj_type == "spike": self.spikes.append(pygame.Rect(*data))
                elif obj_type == "checkpoint": self.checkpoints.append(GameObject(data[0], data[1], data[2], data[3], CHECKPOINT_COLOR, "checkpoint"))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q: self.game.change_state(MENU)
                if event.key == pygame.K_j: self.toggle_mode()
                if event.key == pygame.K_SPACE:
                    if self.is_wall_sliding:
                        self.player_vel_y = JUMP_STRENGTH
                        keys = pygame.key.get_pressed()
                        away_from_wall_movement = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) if self.wall_slide_dir == 'left' else (keys[pygame.K_LEFT] or keys[pygame.K_a])
                        push_off_force = 10 if away_from_wall_movement else 5
                        self.player.x += push_off_force if self.wall_slide_dir == 'left' else -push_off_force
                        self.is_wall_sliding = False
                    elif self.is_3d_mode and self.player_z == 0:
                        self.player_vel_z = JUMP_STRENGTH
                if event.key in [pygame.K_UP, pygame.K_w] and not self.is_3d_mode and (self.on_ground or self.coyote_timer > 0):
                    self.player_vel_y = JUMP_STRENGTH
                    self.coyote_timer = 0

    def toggle_mode(self):
        self.is_3d_mode = not self.is_3d_mode
        center = self.player.center
        self.player.size = (40, 40) if self.is_3d_mode else (40, 50)
        self.player.center = center
        for obj in self.pushable_objects: obj.is_static = not self.is_3d_mode
        if not self.is_3d_mode: self.player_vel_y = 0
        self.is_grabbing = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.is_grabbing = keys[pygame.K_k] and self.is_3d_mode
        
        dx = ((keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])) * 5
        dy = 0

        if self.is_wall_sliding:
            self.player_vel_y = min(self.player_vel_y + GRAVITY, 2) # Slower slide
        
        if self.is_3d_mode:
            dy = ((keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])) * 5
            self.player_vel_z += GRAVITY
            self.player_z += self.player_vel_z
            if self.player_z > 0:
                self.player_z = 0
                self.player_vel_z = 0
        else:
            if not self.is_wall_sliding:
                self.player_vel_y += GRAVITY
            dy = self.player_vel_y

        self.player.x += dx
        self.handle_collisions('horizontal', dx)
        self.player.y += dy
        self.handle_collisions('vertical', dy)

        if self.on_ground: self.coyote_timer = COYOTE_TIME_FRAMES
        else: self.coyote_timer -= 1
        
        self.camera.update(self.player)

        if self.player.top > SCREEN_HEIGHT + 50: self.reset_level()
        if self.goal_rect and self.player.colliderect(self.goal_rect):
            print("Level Complete!")
            self.game.change_state(MENU)

    def reset_level(self):
        self.player.topleft = self.last_checkpoint
        self.player_vel_y = 0
        # Reset pushable objects to their initial state if needed
        # For simplicity, we reload the whole level, but a more robust system
        # would reset only dynamic elements.
        self.load_level(self.level_data)

    def handle_collisions(self, axis, movement):
        self.on_ground = False
        self.is_wall_sliding = False

        if not self.is_3d_mode and axis == 'vertical':
            for slope in self.slopes:
                if self.player.colliderect(slope.rect):
                    if 0 <= self.player.centerx - slope.rect.x <= slope.rect.width:
                        slope_y = slope.get_y_at_x(self.player.centerx)
                        if self.player.bottom >= slope_y:
                            self.player.bottom = slope_y; self.on_ground = True; self.player_vel_y = 0
        
        for spike in self.spikes:
            if self.player.colliderect(spike):
                self.reset_level()
                return
        
        for cp in self.checkpoints:
            if self.player.colliderect(cp.rect):
                if self.last_checkpoint != cp.rect.topleft:
                    self.last_checkpoint = cp.rect.topleft
                    cp.color = CHECKPOINT_ACTIVE_COLOR

        static_colliders = self.platforms + [obj.rect for obj in self.pushable_objects if obj.is_static]
        
        # In 3D mode, only collide with walls/slopes if on the ground (z=0)
        if self.is_3d_mode:
            if self.player_z == 0:
                static_colliders += self.walls_3d + self.v_walls + [s.rect for s in self.slopes]
        else:
            static_colliders += self.walls_3d + self.v_walls

        for plat in static_colliders:
            if self.player.colliderect(plat):
                if axis == 'horizontal':
                    if movement > 0: self.player.right = plat.left
                    if movement < 0: self.player.left = plat.right
                elif axis == 'vertical':
                    if movement > 0 and not self.on_ground:
                        self.player.bottom = plat.top; self.on_ground = True; self.player_vel_y = 0
                    if movement < 0: self.player.top = plat.bottom; self.player_vel_y = 0
        
        if not self.is_3d_mode:
            for wall in self.v_walls:
                if self.player.colliderect(wall) and not self.on_ground:
                    if (movement > 0 and self.player.right > wall.left) or \
                       (movement < 0 and self.player.left < wall.right):
                        self.is_wall_sliding = True
                        self.wall_slide_dir = 'left' if movement > 0 else 'right'
                        break
            for tramp in self.trampolines:
                if self.player.colliderect(tramp) and self.player_vel_y > 0:
                    self.player.bottom = tramp.top; self.player_vel_y = TRAMPOLINE_BOUNCE

        if self.is_3d_mode:
            colliders_3d = [s.rect for s in self.slopes]
            if self.player_z == 0: colliders_3d.extend(self.walls_3d)
            for wall in colliders_3d:
                if self.player.colliderect(wall):
                    if axis == 'horizontal':
                        if movement > 0: self.player.right = wall.left
                        if movement < 0: self.player.left = wall.right
                    elif axis == 'vertical':
                        if movement > 0: self.player.bottom = wall.top
                        if movement < 0: self.player.top = wall.bottom
            
            all_static = self.platforms + self.walls_3d + self.v_walls + [s.rect for s in self.slopes]
            for obj in self.pushable_objects:
                if self.player.colliderect(obj.rect):
                    if self.is_grabbing:
                        # Apply movement with damping
                        damp_factor = 0.9
                        move_x = movement * damp_factor
                        move_y = 0
                        if axis == 'vertical':
                            move_x = 0
                            move_y = movement * damp_factor

                        temp_rect = obj.rect.move(move_x, move_y)
                        
                        can_move = True
                        for s in all_static:
                            if temp_rect.colliderect(s):
                                can_move = False
                                break
                        if can_move:
                            obj.rect = temp_rect
                    else:
                        if axis == 'horizontal':
                            if movement > 0: self.player.right = obj.rect.left
                            if movement < 0: self.player.left = obj.rect.right
                        if axis == 'vertical':
                            if movement > 0: self.player.bottom = obj.rect.top
                            if movement < 0: self.player.top = obj.rect.bottom

    def draw(self, screen):
        screen.fill(WHITE)
        
        # Optimization: Create a rect for the visible screen area in world coordinates
        visible_world_rect = pygame.Rect(-self.camera.camera.x, -self.camera.camera.y, SCREEN_WIDTH, SCREEN_HEIGHT)

        for plat in self.platforms:
            if plat.colliderect(visible_world_rect):
                pygame.draw.rect(screen, GREY, self.camera.apply_rect(plat))
        if self.goal_rect and self.goal_rect.colliderect(visible_world_rect):
            goal_surf = pygame.Surface(self.goal_rect.size, pygame.SRCALPHA)
            goal_surf.fill(GOAL_COLOR)
            screen.blit(goal_surf, self.camera.apply_rect(self.goal_rect))
        for cp in self.checkpoints:
            if cp.rect.colliderect(visible_world_rect):
                cp_surf = pygame.Surface(cp.rect.size, pygame.SRCALPHA)
                cp_surf.fill(cp.color)
                screen.blit(cp_surf, self.camera.apply_rect(cp.rect))
        for spike in self.spikes:
            if spike.colliderect(visible_world_rect):
                pts = [(spike.left, spike.bottom), (spike.centerx, spike.top), (spike.right, spike.bottom)]
            cam_pts = [self.camera.apply_rect(pygame.Rect(p, (1,1))).topleft for p in pts]
            pygame.draw.polygon(screen, SPIKE_COLOR, cam_pts)
        for tramp in self.trampolines:
            if tramp.colliderect(visible_world_rect):
                pygame.draw.rect(screen, TRAMPOLINE_COLOR, self.camera.apply_rect(tramp))
        for wall in self.walls_3d:
            if wall.colliderect(visible_world_rect):
                if self.is_3d_mode:
                    shadow_surf = pygame.Surface((wall.width, 10), pygame.SRCALPHA)
                    shadow_surf.fill(WALL_3D_SHADOW_COLOR)
                    screen.blit(shadow_surf, self.camera.apply_rect(wall).move(5, wall.height - 5))
                pygame.draw.rect(screen, WALL_3D_COLOR, self.camera.apply_rect(wall))
        for wall in self.v_walls:
            if wall.colliderect(visible_world_rect):
                pygame.draw.rect(screen, WALL_3D_COLOR, self.camera.apply_rect(wall))
        for slope in self.slopes:
            if slope.rect.colliderect(visible_world_rect):
                slope.draw(screen, self.camera)
        for obj in self.pushable_objects:
            if obj.rect.colliderect(visible_world_rect):
                obj.draw(screen, self.camera)
        
        player_color = GREEN if self.is_3d_mode else BLUE
        if self.is_wall_sliding: player_color = (0, 200, 200) # Cyan when wall sliding
        
        player_draw_rect = self.camera.apply(self.player)

        if self.is_3d_mode:
            # Draw shadow first
            if self.player_z < 0:
                shadow_size = self.player.width
                shadow_rect = pygame.Rect(0, 0, shadow_size, shadow_size // 2)
                shadow_rect.center = player_draw_rect.center
                shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (0,0,0,100), (0,0,shadow_size, shadow_size//2))
                screen.blit(shadow_surf, shadow_rect)

            # Apply Z-based scaling (gets bigger as it comes closer/higher)
            scale = 1 + (abs(self.player_z) / (Z_JUMP_HEIGHT * 4))
            player_draw_rect.width = int(self.player.width * scale)
            player_draw_rect.height = int(self.player.height * scale)
            
            # Apply Z-based offset and keep center
            original_center = self.camera.apply(self.player).center
            player_draw_rect.centerx = original_center[0]
            player_draw_rect.centery = original_center[1] + int(self.player_z)

        pygame.draw.rect(screen, player_color, player_draw_rect)

        font = pygame.font.Font(None, 36)
        mode_text = f"Mode: {'3D (Grab)' if self.is_grabbing else '3D' if self.is_3d_mode else '2D'}"
        screen.blit(font.render(mode_text, True, BLACK), (10, 10))

class PlayingInfinite(Playing):
    def __init__(self, game):
        super().__init__(game, level_data=[])
        self.last_generated_x = 0
        self.generate_chunk(0)

    def reset_level(self):
        self.player.topleft = self.start_pos
        self.player_vel_y = 0
        self.player_z = 0
        self.player_vel_z = 0
        self.last_generated_x = 0
        self.platforms, self.pushable_objects, self.trampolines, self.walls_3d, self.slopes, self.spikes, self.checkpoints, self.v_walls = [], [], [], [], [], [], [], []
        self.platforms.append(pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH * 2, 20))
        self.generate_chunk(0)

    def generate_chunk(self, start_x):
        chunk_width = SCREEN_WIDTH 
        end_x = start_x + chunk_width
        
        patterns = ['flat_gap', 'platforms', 'spike_pit', 'slope_jump', 'wall_climb']
        chosen_pattern = random.choice(patterns)

        if chosen_pattern == 'flat_gap':
            gap_start = start_x + random.randint(100, 300)
            gap_end = gap_start + random.randint(100, 250)
            self.platforms.append(pygame.Rect(start_x - 20, SCREEN_HEIGHT - 40, gap_start - start_x + 20, 40))
            self.platforms.append(pygame.Rect(gap_end, SCREEN_HEIGHT - 40, end_x - gap_end + 20, 40))

        elif chosen_pattern == 'platforms':
            for i in range(random.randint(3, 6)):
                px = start_x + random.randint(0, chunk_width - 100)
                py = random.randint(SCREEN_HEIGHT - 250, SCREEN_HEIGHT - 80)
                self.platforms.append(pygame.Rect(px, py, random.randint(80, 150), 20))

        elif chosen_pattern == 'spike_pit':
            pit_start = start_x + random.randint(100, 200)
            pit_width = random.randint(80, 200)
            self.platforms.append(pygame.Rect(start_x - 20, SCREEN_HEIGHT - 40, pit_start - start_x + 20, 40))
            for i in range(pit_width // 20):
                self.spikes.append(pygame.Rect(pit_start + i * 20, SCREEN_HEIGHT - 40, 20, 20))
            self.platforms.append(pygame.Rect(pit_start + pit_width, SCREEN_HEIGHT - 40, end_x - (pit_start + pit_width) + 20, 40))

        elif chosen_pattern == 'slope_jump':
            sx = start_x + random.randint(100, 200)
            self.slopes.append(Slope(sx, SCREEN_HEIGHT - 120, 100, 100, SLOPE_COLOR, 100, 0))
            if random.random() < 0.5:
                self.platforms.append(pygame.Rect(sx + 200, SCREEN_HEIGHT - 200, 120, 20))

        elif chosen_pattern == 'wall_climb':
            wx = start_x + 150
            self.walls_3d.append(pygame.Rect(wx, SCREEN_HEIGHT - 120, 20, 120))
            self.walls_3d.append(pygame.Rect(wx + 200, SCREEN_HEIGHT - 220, 20, 120))
            self.platforms.append(pygame.Rect(wx + 20, SCREEN_HEIGHT - 220, 180, 20))

        self.last_generated_x = end_x

    def update(self):
        super().update()
        player_world_x = self.player.right - self.camera.camera.x
        if player_world_x > self.last_generated_x:
            self.last_generated_x += SCREEN_WIDTH * 0.75
            self.generate_chunk(self.last_generated_x)
        
        despawn_line = self.player.centerx - SCREEN_WIDTH * 1.5
        self.platforms = [p for p in self.platforms if p.right > despawn_line or p.height == 40] # Keep ground platforms
        self.pushable_objects = [o for o in self.pushable_objects if o.rect.right > despawn_line]
        self.trampolines = [t for t in self.trampolines if t.right > despawn_line]
        self.walls_3d = [w for w in self.walls_3d if w.right > despawn_line]
        self.slopes = [s for s in self.slopes if s.rect.right > despawn_line]
        self.spikes = [s for s in self.spikes if s.right > despawn_line]

# --- Main Game Class ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D/3D Game")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.static_camera = Camera(0,0)
        
        self.states = {
            MENU: Menu(self),
            LEVEL_EDITOR: LevelEditor(self),
            LEVEL_SELECT: LevelSelect(self),
            PLAYING_INFINITE: PlayingInfinite(self)
        }
        self.current_state_name = MENU
        self.current_state = self.states[self.current_state_name]

    def change_state(self, new_state_name, level_data=None):
        if new_state_name in self.states:
            if new_state_name == LEVEL_EDITOR:
                self.states[LEVEL_EDITOR] = LevelEditor(self, level_data=level_data)
            elif new_state_name in [PLAYING_INFINITE, LEVEL_SELECT]:
                self.states[new_state_name] = type(self.states[new_state_name])(self)
            self.current_state = self.states[new_state_name]
            self.current_state_name = new_state_name

    def start_playing(self, level_data=None):
        self.states[PLAYING] = Playing(self, level_data=level_data)
        self.change_state(PLAYING)
        
    def start_editing(self, level_data=None):
        self.change_state(LEVEL_EDITOR, level_data=level_data)

    def run(self):
        while self.is_running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: self.is_running = False
            
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
