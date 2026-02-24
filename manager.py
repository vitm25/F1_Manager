import pygame
import math
import sys
import random
pygame.init() # spusteni knihovny

rozliseni_okna = (1000, 600)
barvy_pozadi = (0, 0, 0,)
FPS = 60
RACE_ARE_WIDTH = 650

RACE_LAPS = 2
race_finished = False
points_awarded = False

#vykreslení okna
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("F1 manažer")

clock = pygame.time.Clock()

GAME_STATE_MENU = "MENU"
GAME_STATE_CHAMPIONSHIP = "CHAMPIONSHIP"
GAME_STATE_PRACTICE = "PRACTICE"
GAME_STATE_SETTINGS = "SETTINGS"
GAME_STATE_RACE = "RACE"
game_state = GAME_STATE_MENU

# tlačítka
buttons = [
    {"text": "CHAMPIONSHIP", "rect": pygame.Rect(300, 200, 300, 60), "action": GAME_STATE_CHAMPIONSHIP},
    {"text": "PRACTICE", "rect": pygame.Rect(300, 280, 300, 60), "action": GAME_STATE_PRACTICE},
    {"text": "SETTINGS", "rect": pygame.Rect(300, 360, 300, 60), "action": GAME_STATE_SETTINGS}
]

WEATHER_CHANGE_TIME = 12.0

race_time = 0.0
font = pygame.font.SysFont("arial", 28)

TIRES = {
    "SOFT": {"pace": -0.3, "wear": 0.04},
    "MEDIUM": {"pace": 0.0, "wear": 0.025},
    "HARD": {"pace": 0.3, "wear": 0.015},
    "INTER": {"pace": 0.6, "wear": 0.02},
    "WET": {"pace": 1.0, "wear": 0.018},
}

POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

WEATHER_TYPES = {
    "SUN": {"lap_modifier": 0.0, "wear_modifier": 1.0},
    "CLOUD": {"lap_modifier": 0.1, "wear_modifier": 1.1},
    "RAIN": {"lap_modifier": 0.8, "wear_modifier": 1.6},
}

class Driver: # jezdec
    def __init__(self, name, base_lap_time, tire):
        self.name = name
        self.base_lap_time = base_lap_time
        
        self.tire = tire
        self.next_tire = tire
        self.tire_wear = 0.0
        
        self.current_lap = 0
        self.total_time = 0.0
        self.lap_timer = 0.0
        
        self.in_pit = False
        self.pit_timer = 0.0
        
        self.last_pit_lap = -999
        self.pit_cooldown_laps = 2
        
        self.pit_error = False
        
        self.points = 0
    
PIT_TIME = 5.0

SAFETY_CAR_DURATION = 8.0
VSC_DURATION = 6.0
RED_FLAG_DURATION = 5.0

#Ai boxy
def ai_should_pit(driver):
    if driver.in_pit:
        return False
    
    if driver.current_lap - driver.last_pit_lap < driver.pit_cooldown_laps:
        return False
    
    if driver.tire_wear > 0.75:
        return True 
    
    if safety_car_active or vsc_active:
        if driver.tire_wear > 0.3:
            return False
    
    if current_weather == "RAIN" and driver.tire not in ["INTER", "WET"]:
        return True
    
    if current_weather == "SUN" and driver.tire in ["INTER", "WET"]:
        return True 
        
    return False

#Ai si vybíra kola
def ai_choose_tire(driver):
    
    if current_weather == "RAIN":
        if random.random() < 0.5:
            return "INTER"
        return "WET"
    
    if driver.current_lap < 5:
        return "SOFT"
    
    if driver.tire_wear > 0.8:
        return "HARD"
    
    return "MEDIUM"

# body z šampionát
def award_championship_points(drivers):
    # seřadíme podle času
    results = sorted(drivers, key=lambda d: d.total_time)
    
    for i, driver in enumerate(results):
        if i < len(POINTS):
            pts = POINTS[i]
            driver.points += pts
            print(f"{driver.name} scored {pts} points")
            
#reset závodu
def reset_race(drivers):
    
    global points_awarded
    points_awarded = False
    
    for d in drivers:
        d.total_time = 0
        d.current_lap = 0
        d.tire_wear = 0
        d.in_pit = False
        d.finished = False
        
# menu
menu_options = ["Championship", "Free Practice", "Settings"]
selected_menu_index = 0

def draw_menu():
    screen.fill((20,20,20))
    mouse_pos = pygame.mouse.get_pos()
    
    for btn in buttons:
        
        color = (255,255,255)
        
        if btn["rect"].collidepoint(mouse_pos):
            color = (255,200,0)
            
        pygame.draw.rect(screen, color, btn["rect"], 2)
        
        text = font.render(btn["text"], True, (255,255,255))
        screen.blit(text, (btn["rect"].x + 20, btn["rect"].y + 15))
        
class Screen:
    def handle_events(self, events):
        pass
    
    def update(self, delta_time):
        pass
    
    def draw(self, screen):
        pass
    
class MenuScreen(Screen):
    # tlačítka
    def __init__(self):
        self.buttons = [
            {"text": "CHAMPIONSHIP", "rect": pygame.Rect(800, 360, 300, 60), "action": GAME_STATE_RACE},
            {"text": "PRACTICE", "rect": pygame.Rect(800, 440, 300, 60), "action": GAME_STATE_PRACTICE},
            {"text": "SETTINGS", "rect": pygame.Rect(800, 520, 300, 60), "action": GAME_STATE_SETTINGS}
        ]
    # eventy
    def handle_events(self, events):
        global current_screen
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                for btn in self.buttons:
                    if btn["rect"].collidepoint(mouse_pos):
                        change_screen(btn["action"])
    # draw                    
    def draw(self, screen):
        screen.fill((50,0,0))
        
        title = font.render("F1 MANAGER", True, (255,255,255))
        screen.blit(title, (870,300))
        
        for btn in self.buttons:
            pygame.draw.rect(screen, (255,255,255), btn["rect"], 2)
            
            text = font.render(btn["text"], True, (255,255,255))
            screen.blit(text, (btn["rect"].x+20, btn["rect"].y+15))

                                    # screen classy
# závod/ championship
class RaceScreen(Screen):
    def __init__(self):
        self.race_time = 0.0 # čas
        
        # počasí
        self.current_weather = "SUN"
        self.weather_timer = 0.0
        
        #safety car/ VSC/ red flag
        self.safety_car_active = False
        self.safety_car_timer = 0.0
        
        self.vsc_active = False
        self.vsc_timer = 0.0
        
        self.red_flag_active = False
        self.red_flag_timer = 0.0
        
        # jezdci
        self.drivers = [
            Driver("Driver A", 3.0, "SOFT"),
            Driver("Driver B", 3.1, "MEDIUM"),
            Driver("Driver C", 3.2, "HARD"),
        ]
        self.selected_driver = self.drivers[0]
        
    # updaty
    def update(self, delta_time):
        
        self.race_time += delta_time
        for driver in self.drivers:
            
            if getattr(driver, "finished", False):
                continue
            
            driver.lap_timer += delta_time
            lap_time = driver.base_lap_time
            
            if driver.lap_timer >= lap_time:
                driver.lap_timer = 0
                driver.current_lap += 1
                driver.total_time += lap_time
                
                if driver.current_lap >= RACE_LAPS:
                    driver.finished = True
                    
        self.weather_timer += delta_time
        
        if self.weather_timer > 12:
            self.weather_timer = 0
            
            roll = random.random()
            
            if roll < 0.6:
                self.current_weather = "SUN"
            elif roll < 0.85:
                self.current_weather = "CLOUD"
            else:
                self.current_weather = "RAIN"
    
    # eventy                
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_screen(GAME_STATE_MENU)
    
    # kreslení
    def draw(self, screen):
        screen.fill((0,100,0))
        
        # race time
        time_text = font.render(f"Race time: {self.race_time:.1f}", True, (255,255,255))
        screen.blit(time_text, (20,20))
        
        # počasí
        weather_text = font.render(f"Weather: {self.current_weather}", True, (255,255,0))
        screen.blit(weather_text, (20,50))
        
        # jezdci
        y = 100
        
            # seřazení podle času
        results = sorted(self.drivers, key=lambda d: d.total_time)
                         
        for i, driver in enumerate(results):
        
            text = font.render(f"p{i+1} {driver.name} | Lap {driver.current_lap}", True, (255, 55, 255))
            
            screen.blit(text, (20,y))
            y += 35

# trénink
class PracticeScreen(Screen):
    def draw(self, screen):
        screen.fill((0,0,100))
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_screen(GAME_STATE_MENU)
# nastavení        
class SettingsScreen(Screen):
    def draw(self, screen):
        screen.fill((100,0,0))
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_screen(GAME_STATE_MENU)
        
#změna okna
current_screen = None

def change_screen(new_state):
    global current_screen, game_state
    
    game_state = new_state
    
    if new_state == GAME_STATE_MENU:
        current_screen = MenuScreen()
        
    elif new_state == GAME_STATE_RACE:
        current_screen = RaceScreen()
    
    elif new_state == GAME_STATE_PRACTICE:
        current_screen = PracticeScreen()
        
    elif new_state == GAME_STATE_SETTINGS:
        current_screen = SettingsScreen()
        
change_screen(GAME_STATE_MENU)

# vykreslovaci smycka / main loop
while True:
    delta_time = clock.tick(FPS) / 1000
    events = pygame.event.get()
    
    # kontrola vypnutí hry
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    current_screen.handle_events(events)
    current_screen.update(delta_time)
    current_screen.draw(screen)
    
    pygame.display.flip()