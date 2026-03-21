import pygame
import math
import sys
import random
from tracks_data import tracks
from championship_data import TEAMS, DRIVER_BASE_TIMES, CALENDAR_2025
pygame.init() # spusteni knihovny

WIDTH = 1920
HEIGHT = 1080
barvy_pozadi = (0, 0, 0,)
FPS = 60
RACE_ARE_WIDTH = 650

pit_entry_index = 5

race_finished = False
points_awarded = False

#vykreslení okna
screen = pygame.display.set_mode([WIDTH, HEIGHT])
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

class Team:
    def __init__(self, name, drivers, color):
        self.name = name
        self.drivers = drivers  # seznam Driver objektů
        self.color = color
        self.points = 0
    
    def get_total_points(self):
        return sum(d.points for d in self.drivers)
    
    def update_points(self):
        self.points = self.get_total_points()

class Driver: # jezdec
    def __init__(self, name, base_lap_time, tire, team_name=None):
        self.name = name
        self.team_name = team_name
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
        self.race_points = 0  # body z jednoho závodu
        
        self.pace_mode = "NEUTRAL"
        self.ai_decision_timer = 0.0
        
        self.base_speed = random.uniform(0.95, 1.05)
        self.overtake_skill = random.uniform(0.8, 1.2)
        
        self.distance = 0.0
        self.drs_active = False

        self.track_index = 0
        self.progress = 0
        self.angle = 0
        self.finished = False

        self.pit_requested = False
        self.on_pit_lane = False
        self.pit_lane_index = 0
        self.pit_lane_progress = 0.0

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

def calculate_gaps(drivers, track):
    
    path_len = len(track["racing_line"])
    laps = track["laps"]
    
    # Průměrný čas na kolo (použijeme později reálný)
    avg_lap = 90.0  # vteřin – upravíš podle trati
    
    results = []
    leader_lap = max(d.current_lap for d in drivers)
    
    for d in drivers:
        position = d.current_lap * path_len + d.track_index + d.progress
        # Odhad času
        completed_laps_time = d.total_time if d.total_time > 0 else d.current_lap * avg_lap
        remaining = (laps - d.current_lap) * avg_lap + (1 - d.progress) * (avg_lap / path_len)
        
        est_total = completed_laps_time + remaining
        results.append((d, est_total, position))
    
    results.sort(key=lambda x: x[1])  # seřadíme podle odhadovaného času
    leader_time = results[0][1]
    
    return [(d, est_total - leader_time) for d, est_total, _ in results]

                                     # screen classy
# závod/ championship

class ChampionshipScreen(Screen):
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)
        self.font_big = pygame.font.SysFont("arial", 28)
        self.font_small = pygame.font.SysFont("arial", 16)
        
        # Track display NASTAVIT HNED NA ZAČÁTKU!
        self.track_display_width = 600
        self.track_display_height = 400
        self.track_offset_x = 50
        self.track_offset_y = 150
        self.track_source_width = 1000
        self.track_source_height = 1000
        
        self.scale_x = self.track_display_width / self.track_source_width
        self.scale_y = self.track_display_height / self.track_source_height
        
        self.track_image = None
        self.driver_rects = []
        
        # Championship state
        self.current_race_index = 0
        self.championship_round = 0
        
        self.teams = {}
        self.drivers = []
        self.current_track = None

        self._initialize_championship()

        # Race state
        self.race_time = 0.0
        self.current_weather = "SUN"
        self.weather_timer = 0.0

        self.safety_car_active = False
        self.safety_car_timer = 0.0

        self.vsc_active = False
        self.vsc_timer = 0.0

        self.red_flag_active = False
        self.red_flag_timer = 0.0

        self.selected_driver = None

        # Time control
        self.time_scale = 1
        self.time_modes = [1, 2, 4, 20]
        self.time_index = 0
        self.paused = False

        self._load_race()
        
        # Buttons
        self.speed_buttons = [
            {"text": "1x", "rect": pygame.Rect(720, 500, 60, 40), "speed": 1},
            {"text": "2x", "rect": pygame.Rect(790, 500, 60, 40), "speed": 2},
            {"text": "4x", "rect": pygame.Rect(860, 500, 60, 40), "speed": 4},
            {"text": "20x", "rect": pygame.Rect(930, 500, 60, 40), "speed": 20},
        ]
        
        # UI elements
        self.pit_button = None
        self.push_button = None
        self.neutral_button = None
        self.save_button = None
        self.next_race_button = None
        
        self.race_finished = False
    
    def _initialize_championship(self):
        """Inicializuje všechny týmy a jezdce"""
        self.teams = {}
        self.drivers = []
        
        for team_name, team_data in TEAMS.items():
            team_drivers = []
            
            for driver_name in team_data["drivers"]:
                base_time = DRIVER_BASE_TIMES.get(driver_name, 1.85)
                driver = Driver(driver_name, base_time, "SOFT", team_name)
                team_drivers.append(driver)
                self.drivers.append(driver)
            
            team = Team(team_name, team_drivers, team_data["color"])
            self.teams[team_name] = team
        
        self.selected_driver = self.drivers[0]
    
    def _load_race(self):
        """Load current race from tracks"""
        if self.current_race_index >= len(CALENDAR_2025):
            print("🏆 Sezóna skončila!")
            return
        
        calendar_entry = CALENDAR_2025[self.current_race_index]
        race_name = calendar_entry["name"]
        
        # Mapping kalendáře na trati (podle tvých dat)
        track_mapping = {
            "Australian GP": "Australia",
            "Chinese GP": "China",
            "Japanese GP": "Japan",
            "Bahrain GP": "Bahrain",
            "Saudi Arabian GP": "Saudi Arabia",
            "Miami GP": "Miami",
            "Emilia Romagna GP": "Imola",
            "Monaco GP": "Monaco",
            "Spanish GP": "Spain",
            "Canadian GP": "Canada",
            "Austrian GP": "Austria",
            "British GP": "Silverstone",
            "Belgian GP": "Belgium",
            "Hungarian GP": "Hungary",
            "Dutch GP": "Netherlands",
            "Italian GP": "Monza",
            "Azerbaijan GP": "Azerbaijan",
            "Singapore GP": "Singapore",
            "United States GP": "USA",
            "Mexico City GP": "Mexico",
            "São Paulo GP": "Brazil",
            "Las Vegas GP": "Las Vegas",
            "Qatar GP": "Qatar",
            "Abu Dhabi GP": "Abu Dhabi",
        }
        
        track_name = track_mapping.get(race_name, None)
        
        # Hledej správnou trať
        found_track = None
        if track_name:
            for track in tracks:
                if track["name"] == track_name:
                    found_track = track
                    break
        
        if not found_track and len(tracks) > 0:
            # Fallback
            found_track = tracks[self.current_race_index % len(tracks)]
            print(f"⚠️ Trať nenalezena: {race_name}, používám: {found_track['name']}")
        
        self.current_track = found_track
        
        if not self.current_track:
            print("❌ CHYBA: Žádné tratě nejsou dostupné!")
            return
        
        try:
            self.track_image = pygame.image.load(self.current_track["map"])
            self.track_image = pygame.transform.scale(
                self.track_image,
                (self.track_display_width, self.track_display_height)
            )
        except Exception as e:
            print(f"⚠️ Nelze načíst obrázek trati: {self.current_track['map']}")
            print(f"   Chyba: {e}")
        
        # Reset drivers
        for driver in self.drivers:
            driver.track_index = 0
            driver.progress = 0
            driver.current_lap = 0
            driver.finished = False
            driver.pit_requested = True
            driver.next_tire = ai_choose_tire(driver, self.current_weather)
            driver.tire_wear = 0.0
            driver.race_points = 0
            driver.total_time = 0.0
        
        self.race_time = 0.0
        self.race_finished = False
        self.championship_round += 1
        print(f"\n🏁 Kolo {self.championship_round}/{len(CALENDAR_2025)}: {self.current_track['name']}")
    
    def finish_race(self):
        """Ukončí závod a přidělí body"""
        if self.race_finished:
            return
        
        self.race_finished = True
        
        # Seřadíme podle času
        results = sorted(self.drivers, key=lambda d: d.total_time)
        
        for i, driver in enumerate(results[:10]):
            points = POINTS[i]
            driver.race_points = points
            driver.points += points
            print(f"✓ {i+1}. {driver.name} ({driver.team_name}): +{points} bodů")
        
        # Update týmů
        for team in self.teams.values():
            team.update_points()
    
    def next_race(self):
        """Přejde na další závod"""
        self.current_race_index += 1
        
        if self.current_race_index >= len(CALENDAR_2025):
            print("🏆 Sezóna skončila!")
            return False
        
        self._load_race()
        return True
    
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
                    print("Čas:", self.time_scale, "x")
                
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Výběr jezdce
                for rect, driver in self.driver_rects:
                    if rect.collidepoint(mouse_pos):
                        self.selected_driver = driver
                        print("Vybrán:", driver.name)
                
                # Pit button
                if self.pit_button and self.pit_button.collidepoint(mouse_pos):
                    if self.selected_driver:
                        self.selected_driver.pit_requested = True
                        self.selected_driver.next_tire = self.selected_driver.tire
                        print(self.selected_driver.name, "BOX BOX")
                
                # Pace buttons
                if self.push_button and self.push_button.collidepoint(mouse_pos):
                    if self.selected_driver:
                        self.selected_driver.pace_mode = "PUSH"
                
                if self.neutral_button and self.neutral_button.collidepoint(mouse_pos):
                    if self.selected_driver:
                        self.selected_driver.pace_mode = "NEUTRAL"
                
                if self.save_button and self.save_button.collidepoint(mouse_pos):
                    if self.selected_driver:
                        self.selected_driver.pace_mode = "SAVE"
                
                # Next race button
                if self.race_finished and self.next_race_button and self.next_race_button.collidepoint(mouse_pos):
                    self.next_race()
                
                # Speed buttons
                for button in self.speed_buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self.time_scale = button["speed"]
    
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20)
        self.font_big = pygame.font.SysFont("arial", 28)
        self.font_small = pygame.font.SysFont("arial", 16)
        
        # Track display
        self.track_display_width = 600
        self.track_display_height = 400
        self.track_offset_x = 50
        self.track_offset_y = 150
        
        self.track_image = None
        self.driver_rects = []
        
        # Championship state
        self.current_race_index = 0
        self.championship_round = 0
        
        self.teams = {}
        self.drivers = []
        self.current_track = None

        self._initialize_championship()

        # Race state
        self.race_time = 0.0
        self.current_weather = "SUN"
        self.weather_timer = 0.0

        self.safety_car_active = False
        self.safety_car_timer = 0.0

        self.vsc_active = False
        self.vsc_timer = 0.0

        self.selected_driver = None

        # Time control
        self.time_scale = 1
        self.time_modes = [1, 2, 4, 20]
        self.time_index = 0
        self.paused = False

        self._load_race()
        
        # Buttons
        self.speed_buttons = [
            {"text": "1x", "rect": pygame.Rect(720, 500, 60, 40), "speed": 1},
            {"text": "2x", "rect": pygame.Rect(790, 500, 60, 40), "speed": 2},
            {"text": "4x", "rect": pygame.Rect(860, 500, 60, 40), "speed": 4},
            {"text": "20x", "rect": pygame.Rect(930, 500, 60, 40), "speed": 20},
        ]
        
        self.pit_button = None
        self.push_button = None
        self.neutral_button = None
        self.save_button = None
        self.next_race_button = None
        
        self.race_finished = False
        self.points_awarded = False

    def _initialize_championship(self):
        self.teams = {}
        self.drivers = []
        
        for team_name, team_data in TEAMS.items():
            team_drivers = []
            for driver_name in team_data["drivers"]:
                base_time = DRIVER_BASE_TIMES.get(driver_name, 1.90)
                driver = Driver(driver_name, base_time, "MEDIUM", team_name)
                team_drivers.append(driver)
                self.drivers.append(driver)
            
            team = Team(team_name, team_drivers, team_data["color"])
            self.teams[team_name] = team
        
        self.selected_driver = self.drivers[0] if self.drivers else None

    def _load_race(self):
        if self.current_race_index >= len(CALENDAR_2025):
            print("Sezóna skončila!")
            return
        
        calendar_entry = CALENDAR_2025[self.current_race_index]
        race_name = calendar_entry["name"]
        
        track_mapping = {  # ... tvůj mapping zůstává stejný ...
            # (nepisuji ho celý, nech ho jak máš)
        }
        
        track_name = track_mapping.get(race_name, None)
        found_track = None
        
        if track_name:
            for track in tracks:
                if track["name"] == track_name:
                    found_track = track
                    break
        
        if not found_track and tracks:
            found_track = tracks[self.current_race_index % len(tracks)]
            print(f"Trať nenalezena: {race_name} → používám {found_track['name']}")
        
        self.current_track = found_track
        
        if not self.current_track:
            print("CHYBA: Žádná trať nenalezena!")
            return
        
        try:
            self.track_image = pygame.image.load(self.current_track["map"])
            self.track_image = pygame.transform.scale(
                self.track_image,
                (self.track_display_width, self.track_display_height)
            )
        except Exception as e:
            print(f"Nelze načíst mapu: {e}")
        
        # Reset jezdců – bez automatického pit requestu!
        for driver in self.drivers:
            driver.track_index = 0
            driver.progress = 0.0
            driver.current_lap = 0
            driver.finished = False
            driver.pit_requested = False
            driver.on_pit_lane = False
            driver.in_pit = False
            driver.pit_timer = 0.0
            driver.tire_wear = 0.0
            driver.last_pit_lap = -10               # může pitovat brzy
            driver.next_tire = "MEDIUM"
            driver.tire = "MEDIUM"
            driver.total_time = 0.0
            driver.race_points = 0
            driver.drs_active = False
        
        self.race_time = 0.0
        self.race_finished = False
        self.points_awarded = False
        self.current_weather = "SUN"
        self.safety_car_active = False
        
        self.championship_round += 1
        print(f"→ Kolo {self.championship_round}: {self.current_track['name']}")

    def finish_race(self):
        if self.race_finished:
            return
        
        self.race_finished = True
        
        finished_drivers = [d for d in self.drivers if d.finished]
        finished_drivers.sort(key=lambda d: d.total_time)
        
        for i, driver in enumerate(finished_drivers):
            if i < len(POINTS):
                pts = POINTS[i]
                driver.race_points = pts
                driver.points += pts
                print(f"{i+1}. {driver.name} +{pts} bodů")
        
        for team in self.teams.values():
            team.update_points()
        
        self.points_awarded = True

    def update(self, delta_time):
        if self.paused or not self.current_track or self.race_finished:
            return
        
        delta_time *= self.time_scale
        self.race_time += delta_time

        # Počasí
        self.weather_timer += delta_time
        if self.weather_timer > WEATHER_CHANGE_TIME * 1.5:  # pomalejší změny
            self.weather_timer = 0
            roll = random.random()
            if roll < 0.65:
                self.current_weather = "SUN"
            elif roll < 0.88:
                self.current_weather = "CLOUD"
            else:
                self.current_weather = "RAIN"

        # Safety car – vzácnější
        if random.random() < 0.0008 and not self.safety_car_active:
            self.safety_car_active = True
            self.safety_car_timer = random.uniform(10, 28)
            print("SAFETY CAR nasazen!")

        if self.safety_car_active:
            self.safety_car_timer -= delta_time
            if self.safety_car_timer <= 0:
                self.safety_car_active = False
                print("Safety car pryč")

        path = self.current_track["racing_line"]
        path_len = len(path)
        pit_path = self.current_track.get("pit_lane", [])

        race_progress = max((d.current_lap for d in self.drivers if not d.finished), default=0) / self.current_track["laps"]

        for driver in self.drivers:
            if driver.finished:
                continue

            driver.ai_decision_timer += delta_time

            # AI rozhodnutí
            if driver != self.selected_driver and driver.ai_decision_timer > 1.8:
                driver.pace_mode = ai_choose_pace(driver, race_progress, self.current_weather)
                driver.ai_decision_timer = 0

            if driver != self.selected_driver:
                if ai_should_pit(driver, self) and not driver.pit_requested:
                    driver.pit_requested = True
                    driver.next_tire = ai_choose_tire(driver, self.current_weather)

            # ────────────────────────────────────────────────
            #       HLAVNÍ VÝPOČET RYCHLOSTI – nejdůležitější část
            # ────────────────────────────────────────────────
            tire_bonus = TIRES.get(driver.tire, TIRES["MEDIUM"])["pace"]
            pace_bonus = PACE.get(driver.pace_mode, PACE["NEUTRAL"])["pace"]
            wear_penalty = driver.tire_wear * 0.55
            weather_mod = WEATHER_TYPES.get(self.current_weather, WEATHER_TYPES["SUN"])["lap_modifier"]

            target_lap_time = driver.base_lap_time + tire_bonus + pace_bonus
            target_lap_time *= (1 + wear_penalty + weather_mod)

            if target_lap_time < 1: target_lap_time = 1.0  # pojistka

            segments_per_sec = path_len / target_lap_time

            speed = segments_per_sec

            # DRS, SC, pit lane...
            if driver.drs_active and self.current_weather != "RAIN":
                speed *= 1.13
            if driver.in_pit or driver.on_pit_lane:
                speed *= 0.32
            if self.safety_car_active:
                speed *= 0.52

            driver.progress += speed * delta_time

            # Přechod segmentů + nové kolo
            while driver.progress >= 1.0:
                driver.progress -= 1.0
                driver.track_index = (driver.track_index + 1) % path_len
                
                if driver.track_index == 0:
                    driver.current_lap += 1
                    driver.total_time = self.race_time   # aktualizujeme čas při přejetí cíle
                    
                    if driver.current_lap >= self.current_track["laps"]:
                        driver.finished = True
                        if not driver.total_time:
                            driver.total_time = self.race_time

            # Opotřebení pneumatik
            wear_rate = PACE[driver.pace_mode]["wear"] * TIRES[driver.tire]["wear"]
            driver.tire_wear += delta_time * wear_rate * 0.018
            driver.tire_wear = min(1.0, driver.tire_wear)

            # Pit lane logika (zjednodušená)
            if driver.in_pit:
                driver.pit_timer += delta_time
                if driver.pit_timer >= PIT_TIME:
                    driver.in_pit = False
                    driver.tire = driver.next_tire
                    driver.tire_wear = 0.0
                    driver.pit_requested = False
                    driver.last_pit_lap = driver.current_lap
                    # vrátí se na trať ~5–8 segmentů po pit exitu
                    driver.track_index = (driver.track_index + 6) % path_len
                    driver.progress = 0.0

        self.update_drs()
        self.handle_battles()

        if all(d.finished for d in self.drivers):
            self.finish_race()
    
    def update_drs(self):
        ordered = sorted(self.drivers, key=lambda d: (d.current_lap, d.distance), reverse=True)
        
        for i, driver in enumerate(ordered):
            driver.drs_active = False
            
            if i == 0:
                continue
            
            front = ordered[i - 1]
            gap = front.distance - driver.distance
            
            if (gap < 25 and self.current_weather != "RAIN" and self.race_time > 5):
                driver.drs_active = True
    
    def handle_battles(self):
        path_len = len(self.current_track["racing_line"])
        
        ordered = sorted(
            self.drivers,
            key=lambda d: d.current_lap * path_len + d.track_index + d.progress,
            reverse=True
        )
        
        for i in range(len(ordered) - 1):
            front = ordered[i]
            behind = ordered[i + 1]
            
            front_pos = front.current_lap * path_len + front.track_index + front.progress
            behind_pos = behind.current_lap * path_len + behind.track_index + behind.progress
            
            gap = front_pos - behind_pos
            
            if 0 < gap < 0.8:
                front_speed = get_speed(front, self)
                behind_speed = get_speed(behind, self)
                
                attack_chance = 0.02 * behind.overtake_skill
                
                if behind.drs_active:
                    attack_chance *= 1.5
                
                if behind_speed > front_speed and random.random() < attack_chance:
                    behind.track_index = front.track_index
                    behind.progress = min(front.progress + 0.05, 0.99)
                    
                    if behind.progress >= 1:
                        behind.progress -= 1
                        behind.track_index = (behind.track_index + 1) % path_len
                    
                    print(f"⚡ {behind.name} předjel {front.name}")
    
    def draw(self, screen):
        screen.fill((0, 100, 0))
        
        # Race info
        time_text = self.font_big.render(f"Čas: {self.race_time:.1f}s", True, (255, 255, 255))
        screen.blit(time_text, (20, 20))
        
        speed_text = self.font.render(f"Rychlost: {self.time_scale}x", True, (255, 255, 255))
        screen.blit(speed_text, (20, 60))
        
        weather_text = self.font.render(f"Počasí: {self.current_weather}", True, (255, 255, 0))
        screen.blit(weather_text, (20, 90))
        
        if self.safety_car_active:
            sc_text = self.font.render("🚗 SAFETY CAR", True, (255, 200, 0))
            screen.blit(sc_text, (20, 120))
        
        race_round = self.font.render(f"Kolo {self.championship_round}: {self.current_track['name']}", True, (255, 255, 255))
        screen.blit(race_round, (20, 150))
        
        # Leaderboard – upravené gapy
        y = 200
        self.driver_rects = []
        
        # Seřadíme podle pozice (nejlepší první)
        ordered = sorted(self.drivers, key=lambda d: 
            d.current_lap * 10000 + d.track_index * 100 + d.progress * 100, reverse=True)
        
        leader_lap = ordered[0].current_lap
        leader_prog = ordered[0].track_index + ordered[0].progress
        
        for i, driver in enumerate(ordered):
            rect = pygame.Rect(20, y, 420, 32)
            self.driver_rects.append((rect, driver))
            
            if driver == self.selected_driver:
                pygame.draw.rect(screen, (70, 70, 90), rect)
            
            if driver.finished:
                gap_str = f"({driver.total_time:.1f}s)"
            elif driver.current_lap == leader_lap:
                gap_raw = (leader_prog - (driver.track_index + driver.progress)) * (90 / len(self.current_track["racing_line"]))
                gap_str = f"+{gap_raw:.1f}s"
            else:
                laps_down = leader_lap - driver.current_lap
                gap_str = f"+{laps_down} kolo" if laps_down == 1 else f"+{laps_down} kol"
            
            color = self.teams.get(driver.team_name, (200,200,200)).color
            drs = " DRS" if driver.drs_active else ""
            
            text = self.font.render(
                f"P{i+1} {driver.name}{drs} | {gap_str}",
                True, color
            )
            screen.blit(text, (28, y + 6))
            y += 36
        
        # Paused
        if self.paused:
            pause_text = self.font_big.render("POZASTAVENO", True, (255, 0, 0))
            screen.blit(pause_text, (450, 50))
        
        # Manager panel
        if self.selected_driver:
            panel_x = 700
            panel_rect = pygame.Rect(panel_x, 0, 300, 500)
            pygame.draw.rect(screen, (30, 30, 30), panel_rect)
            pygame.draw.line(screen, (80, 80, 80), (panel_x, 0), (panel_x, 500), 2)
            
            selected = self.selected_driver
            team_color = self.teams[selected.team_name].color
            
            name_text = self.font_big.render(f"{selected.name}", True, team_color)
            screen.blit(name_text, (panel_x + 20, 40))
            
            team_text = self.font.render(f"Tým: {selected.team_name}", True, (200, 200, 200))
            screen.blit(team_text, (panel_x + 20, 80))
            
            tire_text = self.font.render(f"Pneumatika: {selected.tire}", True, (255, 255, 255))
            screen.blit(tire_text, (panel_x + 20, 120))
            
            wear_percent = int(selected.tire_wear * 100)
            wear_text = self.font.render(f"Opotřebení: {wear_percent}%", True, (255, 100, 100) if wear_percent > 80 else (255, 255, 255))
            screen.blit(wear_text, (panel_x + 20, 150))
            
            self.pit_button = pygame.Rect(panel_x + 20, 200, 150, 45)
            pygame.draw.rect(screen, (200, 50, 50), self.pit_button)
            pit_text = self.font.render("BOX BOX", True, (255, 255, 255))
            screen.blit(pit_text, (panel_x + 40, 210))
            
            pace_text = self.font.render(f"Styl jízdy: {selected.pace_mode}", True, (255, 255, 0))
            screen.blit(pace_text, (panel_x + 20, 290))
            
            self.push_button = pygame.Rect(panel_x + 20, 250, 70, 35)
            self.neutral_button = pygame.Rect(panel_x + 95, 250, 70, 35)
            self.save_button = pygame.Rect(panel_x + 170, 250, 70, 35)
            
            pygame.draw.rect(screen, (200, 60, 60), self.push_button)
            pygame.draw.rect(screen, (120, 120, 120), self.neutral_button)
            pygame.draw.rect(screen, (60, 120, 200), self.save_button)
            
            screen.blit(self.font.render("PUSH", True, (255, 255, 255)), (panel_x + 25, 255))
            screen.blit(self.font.render("NEUTRAL", True, (255, 255, 255)), (panel_x + 100, 255))
            screen.blit(self.font.render("SAVE", True, (255, 255, 255)), (panel_x + 172, 255))
            
            points_text = self.font.render(f"Body z závodu: {selected.race_points}", True, (255, 200, 0))
            screen.blit(points_text, (panel_x + 20, 340))
            
            total_points_text = self.font.render(f"Celkem: {selected.points}", True, (255, 200, 0))
            screen.blit(total_points_text, (panel_x + 20, 370))
        
        # Track display
        if self.track_image:
            screen.blit(self.track_image, (self.track_offset_x, self.track_offset_y))
            
            path = self.current_track["racing_line"]
            
            # DRS zones
            for start, end in self.current_track["drs_zones"]:
                a = min(start, end)
                b = max(start, end)
                
                for i in range(a, min(b, len(path) - 1)):
                    x1, y1 = path[i]
                    x2, y2 = path[i + 1]
                    
                    x1 = x1 * self.scale_x + self.track_offset_x
                    y1 = y1 * self.scale_y + self.track_offset_y
                    x2 = x2 * self.scale_x + self.track_offset_x
                    y2 = y2 * self.scale_y + self.track_offset_y
                    
                    pygame.draw.line(screen, (0, 200, 255), (x1, y1), (x2, y2), 4)
            
            # Pit lane
            if len(self.current_track["pit_lane"]) > 1:
                scaled_pit = []
                for px, py in self.current_track["pit_lane"]:
                    sx = px * self.scale_x + self.track_offset_x
                    sy = py * self.scale_y + self.track_offset_y
                    scaled_pit.append((sx, sy))
                
                pygame.draw.lines(screen, (255, 140, 0), False, scaled_pit, 3)
            
            # Racing line
            for p in path:
                px = int(p[0] * self.scale_x + self.track_offset_x)
                py = int(p[1] * self.scale_y + self.track_offset_y)
                pygame.draw.circle(screen, (0, 255, 255), (px, py), 3)
            
            # Cars on track
            for driver in self.drivers:
                i = driver.track_index
                next_i = (i + 1) % len(path)
                
                x1, y1 = path[i]
                x2, y2 = path[next_i]
                
                x1 = x1 * self.scale_x
                y1 = y1 * self.scale_y
                x2 = x2 * self.scale_x
                y2 = y2 * self.scale_y
                
                x = x1 + (x2 - x1) * driver.progress + self.track_offset_x
                y = y1 + (y2 - y1) * driver.progress + self.track_offset_y
                
                dx = x2 - x1
                dy = y2 - y1
                driver.angle = math.degrees(math.atan2(dy, dx))
                
                color = self.teams[driver.team_name].color
                if driver == self.selected_driver:
                    pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 8)
                
                pygame.draw.circle(screen, color, (int(x), int(y)), 6)
        
        # Speed buttons
        for button in self.speed_buttons:
            color = (80, 80, 80)
            if button["speed"] == self.time_scale:
                color = (200, 200, 0)
            
            pygame.draw.rect(screen, color, button["rect"])
            text_cas = self.font.render(button["text"], True, (255, 255, 255))
            text_rect = text_cas.get_rect(center=button["rect"].center)
            screen.blit(text_cas, text_rect)
        
        # Championship standings
        y = 0
        stand_title = self.font_big.render("CHAMPIONSHIP STANDINGS", True, (255, 255, 0))
        screen.blit(stand_title, (1550, y))
        y += 40
        
        standings = sorted(self.teams.values(), key=lambda t: t.points, reverse=True)
        for i, team in enumerate(standings[:10]):
            team_text = self.font.render(f"{i+1}. {team.name}: {team.points}pts", True, team.color)
            screen.blit(team_text, (1550, y))
            y += 30
        
        # Race finished
        if self.race_finished:
            finish_rect = pygame.Rect(600, 400, 700, 200)
            pygame.draw.rect(screen, (30, 30, 30), finish_rect)
            pygame.draw.rect(screen, (255, 255, 0), finish_rect, 3)
            
            finish_text = self.font_big.render("ZÁVOD SKONČIL", True, (255, 200, 0))
            screen.blit(finish_text, (750, 430))
            
            self.next_race_button = pygame.Rect(750, 490, 300, 60)
            pygame.draw.rect(screen, (100, 200, 100), self.next_race_button)
            next_text = self.font.render("Další závod (KLIKNI)", True, (255, 255, 255))
            text_rect = next_text.get_rect(center=self.next_race_button.center)
            screen.blit(next_text, text_rect)

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
        current_screen = ChampionshipScreen()
    
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