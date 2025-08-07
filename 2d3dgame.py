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
WALL_3D_SHADOW_COLOR = (0, 0, 0, 100) # Semi-transparent black
SLOPE_COLOR = (255, 165, 0) # Orange

# --- Physics ---
GRAVITY = 0.5
JUMP_STRENGTH = -11
TRAMPOLINE_BOUNCE = -20
COYOTE_TIME_FRAMES = 4

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
        self.buttons = []
        self.levels_dir = "levels"
        self.load_levels()
        self.back_button = Button(30, SCREEN_HEIGHT - 70, 150, 50, "Back", GREY, HOVER_GREY)
    def load_levels(self):
        if not os.path.exists(self.levels_dir): os.makedirs(self.levels_dir)
        level_files = [f for f in os.listdir(self.levels_dir) if f.endswith(".txt")]
        for i, filename in enumerate(level_files):
            self.buttons.append(Button(SCREEN_WIDTH // 2 - 150, 100 + i * 60, 300, 50, filename[:-4], LIGHT_GREY, HOVER_GREY))
    def handle_events(self, events):
        for event in events:
            if self.back_button.is_clicked(event): self.game.change_state(MENU)
            for button in self.buttons:
                if button.is_clicked(event):
                    with open(os.path.join(self.levels_dir, f"{button.text}.txt"), 'r') as f:
                        self.game.start_playing(level_data=f.readlines())
    def update(self):
        super().update()
        self.back_button.check_hover(pygame.mouse.get_pos())
    def draw(self, screen):
        screen.fill(WHITE)
        title_font = pygame.font.Font(None, 74)
        title_surf = title_font.render("Select a Level", True, BLACK)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 50)))
        self.back_button.draw(screen, self.font)
        for button in self.buttons: button.draw(screen, self.font)

# --- Level Editor ---
class LevelEditor(LevelSelect):
    def __init__(self, game):
        super().__init__(game)
        self.objects = [GameObject(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20, GREY, "ground")]
        self.selected_object_type = None
        self.snap_to_grid = True
        self.ui_width = 200
        
        self.palette_buttons = [
            Button(10, 50, 180, 40, "Platform", RED, (255, 100, 100)),
            Button(10, 100, 180, 40, "Pushable Box", PURPLE, (200, 100, 200)),
            Button(10, 150, 180, 40, "Trampoline", TRAMPOLINE_COLOR, (100, 200, 200)),
            Button(10, 200, 180, 40, "3D Wall", WALL_3D_COLOR, (150, 150, 255)),
            Button(10, 250, 180, 40, "Slope Up", SLOPE_COLOR, (255, 200, 100)),
            Button(10, 300, 180, 40, "Slope Down", SLOPE_COLOR, (255, 200, 100)),
            Button(10, 350, 180, 40, "DELETE", (255, 50, 50), (255, 120, 120))
        ]
        self.snap_button = Button(10, 420, 180, 40, "Snap: ON", GREEN, (100, 255, 100))
        self.save_button = Button(10, SCREEN_HEIGHT - 60, 180, 40, "Save Level", GREEN, (100, 255, 100))
        self.back_button = Button(10, SCREEN_HEIGHT - 110, 180, 40, "Back to Menu", GREY, HOVER_GREY)

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if self.back_button.is_clicked(event): self.game.change_state(MENU)
            if self.snap_button.is_clicked(event):
                self.snap_to_grid = not self.snap_to_grid
                self.snap_button.text = f"Snap: {'ON' if self.snap_to_grid else 'OFF'}"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(self.palette_buttons):
                    if btn.is_clicked(event):
                        self.selected_object_type = ["platform", "pushable", "trampoline", "wall_3d", "slope_up", "slope_down", "delete"][i]
                        return
                if self.save_button.is_clicked(event): self.save_level(); return

                if mouse_pos[0] > self.ui_width:
                    if event.button == 1:
                        if self.selected_object_type == "delete": self.delete_object(mouse_pos)
                        else: self.place_object(mouse_pos)
                else: self.selected_object_type = None

    def place_object(self, pos):
        if self.selected_object_type is None: return
        x, y = pos
        if self.snap_to_grid:
            x = (x // GRID_SIZE) * GRID_SIZE
            y = (y // GRID_SIZE) * GRID_SIZE
        
        if self.selected_object_type == "platform": self.objects.append(GameObject(x, y, 100, 20, RED, "platform"))
        elif self.selected_object_type == "pushable": self.objects.append(PushableObject(x, y, 40, 40, PURPLE))
        elif self.selected_object_type == "trampoline": self.objects.append(GameObject(x, y, 80, 20, TRAMPOLINE_COLOR, "trampoline"))
        elif self.selected_object_type == "wall_3d": self.objects.append(GameObject(x, y, 20, 100, WALL_3D_COLOR, "wall_3d"))
        elif self.selected_object_type == "slope_up": self.objects.append(Slope(x, y, 100, 100, SLOPE_COLOR, 100, 0))
        elif self.selected_object_type == "slope_down": self.objects.append(Slope(x, y, 100, 100, SLOPE_COLOR, 0, 100))

    def delete_object(self, pos):
        self.objects = [o for o in self.objects if not o.rect.collidepoint(pos) and o.type != "ground"]

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.palette_buttons: button.check_hover(mouse_pos)
        self.save_button.check_hover(mouse_pos)
        self.back_button.check_hover(mouse_pos)
        self.snap_button.check_hover(mouse_pos)

    def draw(self, screen):
        screen.fill(WHITE)
        self.draw_grid(screen)
        for obj in self.objects:
            if isinstance(obj, Slope): obj.draw(screen, self.game.static_camera)
            else: pygame.draw.rect(screen, obj.color, obj.rect)
        self.draw_ghost(screen)
        ui_panel = pygame.Rect(0, 0, self.ui_width, SCREEN_HEIGHT)
        pygame.draw.rect(screen, UI_PANEL_COLOR, ui_panel)
        title_surf = self.font.render("Editor", True, BLACK)
        screen.blit(title_surf, (10, 10))
        for button in self.palette_buttons: button.draw(screen, self.font)
        self.snap_button.draw(screen, self.font)
        self.save_button.draw(screen, self.font)
        self.back_button.draw(screen, self.font)

    def draw_grid(self, screen):
        if self.snap_to_grid:
            for x in range(0, SCREEN_WIDTH, GRID_SIZE): pygame.draw.line(screen, LIGHT_GREY, (x, 0), (x, SCREEN_HEIGHT))
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
        elif self.selected_object_type == "delete":
            pygame.draw.line(screen, RED, (x - 10, y - 10), (x + 10, y + 10), 3)
            pygame.draw.line(screen, RED, (x - 10, y + 10), (x + 10, y - 10), 3)

    def save_level(self):
        if not os.path.exists("levels"): os.makedirs("levels")
        filename = input("Enter level name to save: ")
        if not filename: return
        with open(os.path.join("levels", f"{filename}.txt"), "w") as f:
            for obj in self.objects:
                if obj.type != "ground":
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
        self.on_ground = False
        self.coyote_timer = 0
        self.is_grabbing = False
        self.platforms, self.pushable_objects, self.trampolines, self.walls_3d, self.slopes = [], [], [], [], []
        self.load_level(level_data)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

    def load_level(self, level_data):
        self.platforms.append(pygame.Rect(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20))
        if level_data:
            for item in level_data:
                parts = item.strip().split(',')
                obj_type, data = parts[0], [int(p) for p in parts[1:]]
                if obj_type == "platform": self.platforms.append(pygame.Rect(*data))
                elif obj_type == "pushable": self.pushable_objects.append(PushableObject(*data, PURPLE))
                elif obj_type == "trampoline": self.trampolines.append(pygame.Rect(*data))
                elif obj_type == "wall_3d": self.walls_3d.append(pygame.Rect(*data))
                elif obj_type == "slope": self.slopes.append(Slope(data[0], data[1], data[2], data[3], SLOPE_COLOR, data[4], data[5]))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.game.change_state(MENU)
                if event.key == pygame.K_SPACE: self.toggle_mode()
                if event.key in [pygame.K_UP, pygame.K_w] and (self.on_ground or self.coyote_timer > 0) and not self.is_3d_mode:
                    self.player_vel_y = JUMP_STRENGTH
                    self.coyote_timer = 0

    def toggle_mode(self):
        self.is_3d_mode = not self.is_3d_mode
        center = self.player.center
        self.player.size = (40, 40) if self.is_3d_mode else (40, 50)
        self.player.center = center
        for obj in self.pushable_objects: obj.is_static = not self.is_3d_mode
        if self.is_3d_mode: self.player_vel_y = 0
        self.is_grabbing = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.is_grabbing = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.is_3d_mode
        
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dx *= 5
        
        dy = 0
        if self.is_3d_mode:
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            dy *= 5
        else:
            self.player_vel_y += GRAVITY
            dy = self.player_vel_y

        self.player.x += dx
        self.handle_collisions('horizontal', dx)
        self.player.y += dy
        self.handle_collisions('vertical', dy)

        if self.on_ground: self.coyote_timer = COYOTE_TIME_FRAMES
        else: self.coyote_timer -= 1
        
        self.camera.update(self.player)

    def handle_collisions(self, axis, movement):
        self.on_ground = False
        if not self.is_3d_mode and axis == 'vertical':
            for slope in self.slopes:
                if self.player.colliderect(slope.rect):
                    if 0 <= self.player.centerx - slope.rect.x <= slope.rect.width:
                        slope_y = slope.get_y_at_x(self.player.centerx)
                        if self.player.bottom >= slope_y:
                            self.player.bottom = slope_y
                            self.on_ground = True
                            self.player_vel_y = 0
        
        static_colliders = self.platforms + [obj.rect for obj in self.pushable_objects if obj.is_static]
        for plat in static_colliders:
            if self.player.colliderect(plat):
                if axis == 'horizontal':
                    if movement > 0: self.player.right = plat.left
                    if movement < 0: self.player.left = plat.right
                elif axis == 'vertical':
                    if movement > 0 and not self.on_ground:
                        self.player.bottom = plat.top
                        self.on_ground = True
                        self.player_vel_y = 0
                    if movement < 0: self.player.top = plat.bottom; self.player_vel_y = 0
        
        if not self.is_3d_mode:
            for tramp in self.trampolines:
                if self.player.colliderect(tramp) and self.player_vel_y > 0:
                    self.player.bottom = tramp.top; self.player_vel_y = TRAMPOLINE_BOUNCE

        if self.is_3d_mode:
            colliders_3d = self.walls_3d + [s.rect for s in self.slopes]
            for wall in colliders_3d:
                if self.player.colliderect(wall):
                    if axis == 'horizontal':
                        if movement > 0: self.player.right = wall.left
                        if movement < 0: self.player.left = wall.right
                    elif axis == 'vertical':
                        if movement > 0: self.player.bottom = wall.top
                        if movement < 0: self.player.top = wall.bottom
            for obj in self.pushable_objects:
                if self.player.colliderect(obj.rect):
                    if self.is_grabbing:
                        if axis == 'horizontal': obj.rect.x += movement
                        if axis == 'vertical': obj.rect.y += movement
                    else:
                        if axis == 'horizontal':
                            if movement > 0: self.player.right = obj.rect.left
                            if movement < 0: self.player.left = obj.rect.right
                        if axis == 'vertical':
                            if movement > 0: self.player.bottom = obj.rect.top
                            if movement < 0: self.player.top = obj.rect.bottom

    def draw(self, screen):
        screen.fill(WHITE)
        for plat in self.platforms: pygame.draw.rect(screen, GREY, self.camera.apply_rect(plat))
        for tramp in self.trampolines: pygame.draw.rect(screen, TRAMPOLINE_COLOR, self.camera.apply_rect(tramp))
        for wall in self.walls_3d:
            if self.is_3d_mode:
                shadow_surf = pygame.Surface((wall.width, 10), pygame.SRCALPHA)
                shadow_surf.fill(WALL_3D_SHADOW_COLOR)
                screen.blit(shadow_surf, self.camera.apply_rect(wall).move(5, wall.height - 5))
            pygame.draw.rect(screen, WALL_3D_COLOR, self.camera.apply_rect(wall))
        for slope in self.slopes: slope.draw(screen, self.camera)
        for obj in self.pushable_objects: obj.draw(screen, self.camera)
        
        player_color = GREEN if self.is_3d_mode else BLUE
        pygame.draw.rect(screen, player_color, self.camera.apply(self.player))

        font = pygame.font.Font(None, 36)
        mode_text = f"Mode: {'3D (Grab)' if self.is_grabbing else '3D' if self.is_3d_mode else '2D'}"
        screen.blit(font.render(mode_text, True, BLACK), (10, 10))

class PlayingInfinite(Playing):
    def __init__(self, game):
        super().__init__(game, level_data=[])
        self.last_generated_x = 0
        self.generate_chunk(SCREEN_WIDTH)

    def generate_chunk(self, x_pos):
        # Ground/Ceiling sections
        if random.random() < 0.2:
            self.platforms.append(pygame.Rect(x_pos, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20))
        if random.random() < 0.1:
            self.platforms.append(pygame.Rect(x_pos, 0, SCREEN_WIDTH, 20))
        
        # Standard platforms
        for _ in range(random.randint(2, 4)):
            self.platforms.append(pygame.Rect(x_pos + random.randint(-100, 100), random.randint(200, SCREEN_HEIGHT - 100), random.randint(80, 200), 20))
        
        # Other objects
        if random.random() < 0.15: self.trampolines.append(pygame.Rect(x_pos + random.randint(0, 100), random.randint(300, SCREEN_HEIGHT - 50), 80, 20))
        if random.random() < 0.1: self.pushable_objects.append(PushableObject(x_pos + random.randint(0, 100), SCREEN_HEIGHT - 60, 40, 40, PURPLE))
        if random.random() < 0.3: self.walls_3d.append(pygame.Rect(x_pos + random.randint(0, 200), SCREEN_HEIGHT - 120, 20, 100))
        if random.random() < 0.2:
            sx, sy = x_pos + random.randint(0, 100), random.randint(300, SCREEN_HEIGHT - 120)
            if random.random() < 0.5: self.slopes.append(Slope(sx, sy, 100, 100, SLOPE_COLOR, 100, 0))
            else: self.slopes.append(Slope(sx, sy, 100, 100, SLOPE_COLOR, 0, 100))

    def update(self):
        super().update()
        player_world_x = self.player.right - self.camera.camera.x
        if player_world_x > self.last_generated_x:
            self.last_generated_x += SCREEN_WIDTH * 0.75
            self.generate_chunk(self.last_generated_x)
        
        despawn_line = self.player.centerx - SCREEN_WIDTH * 1.5
        self.platforms = [p for p in self.platforms if p.right > despawn_line or p.height == 20]
        self.pushable_objects = [o for o in self.pushable_objects if o.rect.right > despawn_line]
        self.trampolines = [t for t in self.trampolines if t.right > despawn_line]
        self.walls_3d = [w for w in self.walls_3d if w.right > despawn_line]
        self.slopes = [s for s in self.slopes if s.rect.right > despawn_line]

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

    def change_state(self, new_state_name):
        if new_state_name in self.states:
            if new_state_name in [PLAYING_INFINITE, LEVEL_SELECT, LEVEL_EDITOR]:
                self.states[new_state_name] = type(self.states[new_state_name])(self)
            self.current_state = self.states[new_state_name]
            self.current_state_name = new_state_name

    def start_playing(self, level_data=None):
        self.states[PLAYING] = Playing(self, level_data=level_data)
        self.change_state(PLAYING)

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
