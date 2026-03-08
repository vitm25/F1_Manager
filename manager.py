import pygame
import math
import sys
import random
from tracks import tracks
pygame.init() # spusteni knihovny

WIDTH = 1920
HEIGHT = 1080
barvy_pozadi = (0, 0, 0,)
FPS = 60
RACE_ARE_WIDTH = 650

RACE_LAPS = 20
race_finished = False
points_awarded = False

#vykreslení okna
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption("F1 manažer")

clock = pygame.time.Clock()

#načtení tratě
track = pygame.image.load("changing_png/usacota.png")
track = pygame.transform.scale(track,(1080,1080))

track_x = (WIDTH - 1080) // 2
track_y = (HEIGHT - 1080) //2

car_x = WIDTH//2
car_y = HEIGHT//2

speed = 2
angle = 0

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

PACE = {
    "PUSH": {"pace": -0.4, "wear": 1.6},
    "NEUTRAL": {"pace": 0.0, "wear": 1.0},
    "SAVE": {"pace": 0.5, "wear": 0.6},
}

track_map = [
(400,300),
(600,250),
(750,300),
(700,450),
(500,500),
(350,420),
]
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
        
        self.pace_mode = "NEUTRAL"
        self.ai_decision_timer = 0.0
        
        self.base_speed = random.uniform(0.95, 1.05)
        self.overtake_skill = random.uniform(0.8, 1.2)
        
        self.distance = 0.0
        self.drs_active = False
        
# výpočet akt. rychlosti
def get_speed(driver, race):
    
    speed = driver.base_speed
    
    # opotřebení zpomaluje
    speed *= (1 - driver.tire_wear * 0.4)
    
    # počasí
    if race.current_weather == "RAIN":
        if driver.tire == "SOFT":
            speed *= 0.85
        elif driver.tire == "INTER":
            speed *= 1.05
            
    # pit lane
    if driver.in_pit:
        speed *= 0.4
        
    # DRS boost
    if driver.drs_active:
        speed *= 1.15

    # safety car

    if race.safety_car_active:
        speed *= 0.5

    return speed
    
PIT_TIME = 5.0

SAFETY_CAR_DURATION = 8.0
VSC_DURATION = 6.0
RED_FLAG_DURATION = 5.0

#Ai boxy
def ai_should_pit(driver, race):
    if driver.in_pit:
        return False
    
    if driver.current_lap - driver.last_pit_lap < driver.pit_cooldown_laps:
        return False
    
    if driver.tire_wear > 0.75:
        return True 
    
    if race.safety_car_active or race.vsc_active:
        if driver.tire_wear > 0.3:
            return False
    
    if race.current_weather == "RAIN" and driver.tire not in ["INTER", "WET"]:
        return True
    
    if race.current_weather == "SUN" and driver.tire in ["INTER", "WET"]:
        return True 
        
    return False

#Ai si vybíra kola
def ai_choose_tire(driver, current_weather):
    
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
            
def ai_choose_pace(driver, race_progress, current_weather):
    
    # zničené gumy
    if driver.tire_wear > 0.8:
        return "SAVE"
    
    # déšť
    if current_weather == "RAIN":
        return "SAVE"
    
    # start závodu
    if race_progress < 0.3:
        return "NEUTRAL"
    
    # střed závodu
    if race_progress < 0.75:
        if driver.tire_wear < 0.4:
            return "PUSH"
        return "NEUTRAL"
    
    # konec závodu
    return "PUSH"

def calculate_gaps(drivers):
    results = sorted(drivers, key=lambda d: d.total_time)
    
    leader_time = results[0].total_time
    
    gaps = []
    for d in results:
        gap = d.total_time - leader_time
        gaps.append((d, gap))
        
    return gaps



    return int(x), int(y)

                                    # screen classy
# závod/ championship
class RaceScreen(Screen):
    def __init__(self):
        
        self.font = pygame.font.SysFont("arial", 22)
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
            Driver("Driver C", 3.0, "SOFT"),
        ]
        self.selected_driver = self.drivers[0]
        
        # ovládání času
        self.time_scale = 1
        self.time_modes = [1,2,4,20]
        self.time_index = 0
        self.paused = False
        
        # tlačítka na ovládání rychlosti
        self.speed_buttons = [
            {"text":"1x", "rect":pygame.Rect(720,500,60,40), "speed":1},
            {"text":"2x", "rect":pygame.Rect(790,500,60,40), "speed":2},
            {"text":"4x", "rect":pygame.Rect(860,500,60,40), "speed":4},
            {"text":"20x", "rect":pygame.Rect(930,500,60,40), "speed":20},
        ]

        # tratě
        self.current_track_index = 0
        self.tracks = tracks

        self.track = self.tracks[self.current_track_index]

        self.track_map = self.track["map"]
        self.track_length = self.track["length"]
        self.race_laps = self.track["laps"]
        
        self.track_image = pygame.image.load(self.track["image"])
        self.track_image = pygame.transform.scale(self.track_image, (600,400))

        self.championship_points = {}
        
        print(self.track)
        
    def update_drs(self):
    
        #seřazení podle pozice na trari
        ordered = sorted(self.drivers, key=lambda d: (d.current_lap, d.distance), reverse=True)
        
        for i, driver in enumerate(ordered):
            
            driver.drs_active = False
            
            # leader nemá drs
            if i == 0:
                continue
            
            front = ordered[i - 1]
    
            gap = front.distance - driver.distance
            
            # DRS podmínky
            if (
                gap < 25 # vzdálenost
                and self.current_weather != "RAIN"
                and self.race_time > 5 # start závodu
            ):
                driver.drs_active = True 

    def finish_race(self):

        for pos, driver in enumerate(self.drivers):

            if pos < 10:
                pts = POINTS[pos]

                if driver.name not in self.championship_points:
                    self.championship_points[driver.name] = 0

                self.championship_points[driver.name] += pts

        self.current_track_index += 1
        
        if self.current_track_index >= len(self.tracks):
            self.current_track_index = 0
            
        self.track = self.tracks[self.current_track_index]
        self.track_map = self.track["map"]
        self.track_length = self.track["length"]
        self.race_laps = self.track["laps"]
        
    # updaty
    def update(self, delta_time):
        
        if self.paused:
            return
        
        delta_time *= self.time_scale 
        
        race_progress = max(d.current_lap for d in self.drivers) / RACE_LAPS
        for driver in self.drivers:
            driver.ai_decision_timer += delta_time
        self.race_time += delta_time
        
        for driver in self.drivers:
            
            if driver != self.selected_driver and driver.ai_decision_timer > 2:
                driver.pace_mode = ai_choose_pace(driver, race_progress, self.current_weather)
                driver.ai_decision_timer = 0
                
            if driver != self.selected_driver:
                if ai_should_pit(driver, self):
                    driver.in_pit = True
                    driver.pit_timer = 0
                    driver.last_pit_lap = driver.current_lap
                    driver.tire = ai_choose_tire(driver, self.current_weather)
                    print(driver.name, "AI PIT STOP")
            
            if getattr(driver, "finished", False):
                continue
            
            speed = get_speed(driver, self)
            driver.distance += speed * delta_time * 100
            
            driver.lap_timer += delta_time
            pace = PACE[driver.pace_mode]
            lap_time = driver.base_lap_time + pace["pace"]
            
            driver.tire_wear += delta_time * 0.02 * pace["wear"]
            driver.tire_wear = min(driver.tire_wear, 1.0)
            
            if driver.lap_timer >= lap_time:
                driver.lap_timer = 0
                driver.current_lap += 1
                driver.total_time += lap_time
                driver.distance = 0
                
                if driver.current_lap >= self.race_laps:
                    driver.finished = True
                    
            if driver.in_pit:
                driver.pit_timer += delta_time
                
                if driver.pit_timer >= PIT_TIME:
                    driver.in_pit = False
                    driver.tire_wear = 0.0
                    driver.tire = random.choice(["SOFT","MEDIUM","HARD"])
                    
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
                
        if random.random() < 0.0005 and not self.safety_car_active:
            self.safety_car_active = True
            self.safety_car_timer = SAFETY_CAR_DURATION
            print("SAFETY CAR DEPLOYED")

        if self.safety_car_active:
            self.safety_car_timer -= delta_time

            if self.safety_car_timer <= 0:
                self.safety_car_active = False
                print("SAFETY CAR IN THIS LAP")

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            angle -=2

        if keys[pygame.K_RIGHT]:
            angle += 2

        if keys[pygame.K_UP]:
            car_x += math.cos(math.radians(angle)) * speed
            car_y += math.sin(math.radians(angle)) * speed

    def handle_battles(self):
        
        # seřadíme podle vzdálenosti
        self.drivers.sort(key=lambda d: (d.current_lap, d.distance), reverse=True)
        
        for i in range(len(self.drivers) - 1):
            
            front = self.drivers[i]
            behind = self.drivers[i + 1]
            
            gap = front.distance - behind.distance
            
            # pokud jsou blízko > boj
            if gap < 5:
                
                front_speed = get_speed(front, self)
                behind_speed = get_speed(behind, self)
                
                attack_chance = 0.02 * behind.overtake_skill
                
                if behind_speed > front_speed and random.random() < attack_chance:
                    
                    # předjetí
                    self.drivers[i], self.drivers[i+1] = behind, front
                    
                    print(front.name, front.distance, "|", behind.name, behind.distance)
                    
        self.update_drs()
    # eventy                
    def handle_events(self, events):
        for event in events:
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_screen(GAME_STATE_MENU)
                    
                if event.key == pygame.K_TAB:
                    self.time_index += 1
                    if self.time_index >= len(self.time_modes):
                        self.time_index = 0
                        
                    self.time_scale = self.time_modes[self.time_index]
                    print("Time speed:", self.time_scale, "x")
                    
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # výběr jezdce
                for rect, driver in self.driver_rects:
                    if rect.collidepoint(mouse_pos):
                        self.selected_driver = driver
                        print("Selected:", driver.name)
                        
                # pit button
                if self.pit_button.collidepoint(mouse_pos):
                    self.selected_driver.in_pit = True
                    self.selected_driver.pit_timer = 0
                    print(self.selected_driver.name, "BOX BOX")
                    
                # pace buttons
                if self.push_button.collidepoint(mouse_pos):
                    self.selected_driver.pace_mode = "PUSH"
                    
                if self.neutral_button.collidepoint(mouse_pos):
                    self.selected_driver.pace_mode = "NEUTRAL"
                    
                if self.save_button.collidepoint(mouse_pos):
                    self.selected_driver.pace_mode = "SAVE"
                    
                # tlačítka na čas
                for button in self.speed_buttons:
                    
                    if button["rect"].collidepoint(mouse_pos):
                        self.time_scale = button["speed"]
    # kreslení
    def draw(self, screen):
        screen.fill((0,100,0))
        
        # race time
        time_text = font.render(f"Race time: {self.race_time:.1f}", True, (255,255,255))
        screen.blit(time_text, (20,20))
        
        # čas
        speed_text = font.render(f"Speed: {self.time_scale}x", True, (255,255,255))
        screen.blit(speed_text, (20,80))
        
        # počasí
        weather_text = font.render(f"Weather: {self.current_weather}", True, (255,255,0))
        screen.blit(weather_text, (20,50))
        
        # jezdci / leaderboard
        y = 125
        self.driver_rects = [] # seznam klikacích oblastí
        
            # seřazení podle času
        results = calculate_gaps(self.drivers)

        for i, (driver, gap) in enumerate(results):
            
            rect = pygame.Rect(20, y, 400, 35)
            self.driver_rects.append((rect, driver))
            
            # zvýraznění vybraného jezdce
            if driver == self.selected_driver:
                pygame.draw.rect(screen, (80,80,80), rect)
                
            if i == 0:
                gap_text = "LEADER"
            else:
                gap_text = f"+{gap:.1f}s"
                
            color = (255,255,0) if i == 0 else (255,255,255)
            drs = "DRS" if driver.drs_active else ""
        
            text = font.render(f"p{i+1} {driver.name} {drs} | {gap_text} | Lap {driver.current_lap}", True, (color))
            
            screen.blit(text, (20,y))
            y += 45
            
        # zmražení času
        if self.paused:
            pause_text = font.render("PAUSED", True, (255,0,0))
            screen.blit(pause_text, (450,50))
            
                                    # panel ovladani
        # box box
        panel_x = 700
        panel_rect = pygame.Rect(panel_x, 0, 300, 600)
        
        pygame.draw.rect(screen, (30,30,30), panel_rect)
        pygame.draw.line(screen, (80,80,80), (panel_x, 0), (panel_x, 600), 2)
        
        driver = self.selected_driver
        
        name_text = font.render(driver.name, True, (255,255,255))
        screen.blit(name_text, (panel_x + 20, 40))
        
        tire_text = font.render(f"Tire: {driver.tire}", True, (255,255,255))
        screen.blit(tire_text, (panel_x + 20, 80))
        
        wear_percent = int(driver.tire_wear * 100)
        wear_text = font.render(f"Wear: {wear_percent}%", True, (255,255,255))
        screen.blit(wear_text, (panel_x + 20, 120))
        
        self.pit_button = pygame.Rect(panel_x +20, 180,200,50)
        
        pygame.draw.rect(screen, (200,50,50), self.pit_button)
        pit_text = font.render("PIT STOP", True, (255,255,255))
        screen.blit(pit_text, (panel_x + 45, 190))
        
        pace_text = font.render(f"Pace: {driver.pace_mode}", True, (255,255,0))
        screen.blit(pace_text, (panel_x + 20,320))
        
        # push, neutral, save
        self.push_button = pygame.Rect(panel_x + 20, 260, 80, 40)
        self.neutral_button = pygame.Rect(panel_x + 110, 260, 80, 40)
        self.save_button = pygame.Rect(panel_x + 200, 260, 80, 40)
        
        pygame.draw.rect(screen, (200,60,60), self.push_button)
        pygame.draw.rect(screen, (120,120,120), self.neutral_button)
        pygame.draw.rect(screen, (60,120,200), self.save_button)
        
        screen.blit(font.render("PUSH", True, (255,255,255)), (panel_x+25, 265))
        screen.blit(font.render("N", True, (255,255,255)), (panel_x+135, 265))
        screen.blit(font.render("SAVE", True, (255,255,255)), (panel_x+205, 265))
        
        screen.blit(self.track_image,(50,150))

        progress = driver.distance / self.track_length

        index = int(progress *(len(self.track_map)-1))
        x,y = self.track_map[index]

        pygame.draw.circle(screen,(255,0,0),(x,y),5)
        
        # vykreslení tlačítek času
        for button in self.speed_buttons:
            
            color = (80,80,80)
            
            if button["speed"] == self.time_scale:
                color = (200,200,0)
                
            pygame.draw.rect(screen, color, button["rect"])
        
            text_cas = self.font.render(button["text"], True, (255,255,255))
            text_rect = text_cas.get_rect(center=button["rect"].center)
            
            screen.blit(text_cas,text_rect)

        
        if self.safety_car_active:
            sc_text = font.render("SAFETY CAR", True, (255,200,0))
            screen.blit(sc_text, (20,110))
            
        track_text = font.render(f"Track: {self.track['name']}", True, (255,255,255))
        screen.blit(track_text, (20,140))

# trénink
class PracticeScreen(Screen):
    def draw(self, screen):
        screen.fill((0,0,100))
        
    # updaty
    def update(self, delta_time):
        pass
    
    # eventy    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_screen(GAME_STATE_MENU)
# nastavení        
class SettingsScreen(Screen):
    def draw(self, screen):
        screen.fill((100,0,0))
        
    # updaty
    def update(self, delta_time):
        pass

    # eventy
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
    
    screen.fill((20,20,20))

    current_screen.draw(screen)
    
    pygame.display.flip()