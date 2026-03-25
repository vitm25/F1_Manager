import pygame
import math
import sys
import random
from tracks_data import tracks
from championship_data import TEAMS, DRIVER_BASE_TIMES, CALENDAR_2025
pygame.init() # spusteni knihovny

print("Dostupné tratě:")
for track in tracks:
    print(f"  - {track['name']}")

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

                # === NOVÉ STRATEGIE ===
        self.current_stint_laps = 0          # kolik kol už jel na těchto gumách
        self.target_stint_end = 0            # na kterém kole plánuje pit
        self.strategy_aggression = random.uniform(0.75, 1.35)  # <1 = konzervativní, >1 = agresivní
        self.planned_stops = random.choice([1, 2])            # 1-stop nebo 2-stop
        self.undercut_chance = 0.0

                # === NOVÉ: PORUCHY A DNF ===
        self.fuel = 1.0                     # 100 %
        self.reliability = random.uniform(0.82, 0.98)   # jak spolehlivé auto
        self.engine_damage = 0.0
        self.is_dnf = False
        self.dnf_reason = None              # "Engine", "Fuel", "Crash", "Spin"
        self.incident_cooldown = 0

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
    if current_weather in ["RAIN", "CLOUD"] and random.random() < 0.8:
        return "INTER" if random.random() < 0.6 else "WET"
    
    # Strategie podle počtu plánovaných zastávek
    if driver.planned_stops == 1:
        return "HARD" if driver.current_lap > 15 else "MEDIUM"
    
    if driver.current_lap < 8:
        return "SOFT"
    elif driver.current_lap < 25:
        return "MEDIUM"
    else:
        return "HARD" if random.random() < 0.7 else "MEDIUM"

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

# ==================== REÁLNÉ STINTY + UNDERCUT / OVERCUT ====================

def ai_plan_stint(driver, race, is_first_stint=True):
    """Nastaví cílovou délku stintu podle typu gum a strategie"""
    tire = driver.tire
    
    base_stint = {
        "SOFT":  random.randint(8,  11),
        "MEDIUM":random.randint(12, 16),
        "HARD":  random.randint(18, 24),
        "INTER": random.randint(6,  10),
        "WET":   random.randint(5,   9),
    }[tire]

    # Agrese + počasí
    modifier = driver.strategy_aggression
    if race.current_weather == "RAIN":
        modifier *= 0.7
    if driver.planned_stops == 1:          # 1-stop = delší stinty
        modifier *= 1.25
    
    driver.target_stint_end = driver.current_lap + int(base_stint * modifier)
    driver.current_stint_laps = 0
    print(f"🧠 {driver.name} plánuje stint do kola {driver.target_stint_end} ({tire})")


def ai_should_pit(driver, race):
    """NOVÁ verze s undercut/overcut logikou"""
    if driver.in_pit or driver.on_pit_lane:
        return False
    if driver.current_lap - driver.last_pit_lap < 6:   # minimální cooldown
        return False

    # Základní podmínky
    if driver.tire_wear > 0.88:
        return True
    if race.current_weather == "RAIN" and driver.tire not in ["INTER", "WET"]:
        return True
    if race.current_weather == "SUN" and driver.tire in ["INTER", "WET"]:
        return True

    # === UNDERCUT / OVERCUT LOGIKA ===
    driver.current_stint_laps += 1   # každé kolo +1

    # Najdeme nejlepšího soupeře před ním
    ahead = None
    min_gap = 999
    for d in race.drivers:
        if d == driver: continue
        gap = (d.current_lap * 100 + d.track_index + d.progress) - \
              (driver.current_lap * 100 + driver.track_index + driver.progress)
        if 0 < gap < min_gap:
            min_gap = gap
            ahead = d

    # UNDERCUT (pitnu dříve než soupeř)
    if ahead and ahead.current_stint_laps > 4 and driver.current_stint_laps >= 7:
        if min_gap < 8 and random.random() < (0.65 * driver.strategy_aggression):
            print(f"🔥 UNDERCUT! {driver.name} pituje před {ahead.name}")
            driver.next_tire = ai_choose_tire(driver, race.current_weather)
            return True

    # OVERCUT (zůstanu déle)
    if driver.current_stint_laps >= driver.target_stint_end - 3:
        if random.random() < 0.4:                     # 40% šance na overcut
            print(f"⏳ OVERCUT {driver.name} – prodlužuji stint")
            driver.target_stint_end += 2
            return False

    # Normální pit podle plánu
    if driver.current_stint_laps >= driver.target_stint_end:
        driver.next_tire = ai_choose_tire(driver, race.current_weather)
        return True

    return False

def generate_incident(driver, race):
    """Snížená šance na incidenty + odstraněno DNF kvůli palivu"""
    if driver.is_dnf or driver.incident_cooldown > 0:
        driver.incident_cooldown = max(0, driver.incident_cooldown - 1)
        return False

    roll = random.random()

    # Velmi nízká šance na jakýkoliv incident
    if roll < 0.004:          # ~1x za 40–50 sekund při 20x
        # Lehká nehoda → Yellow flag
        driver.engine_damage += 0.35
        race.yellow_flag_active = True
        print(f"🟡 ŽLUTÁ VLÁJKA – {driver.name} měl spin!")
        driver.incident_cooldown = 10
        return True

    elif roll < 0.007:        # Motor / Crash
        driver.is_dnf = True
        driver.dnf_reason = random.choice(["Engine", "Crash", "Big Shunt", "Spin + Wall"])
        driver.finished = True
        print(f"💥 DNF – {driver.name} ({driver.dnf_reason})")

        if random.random() < 0.55:
            race.safety_car_active = True
            race.safety_car_timer = random.uniform(12, 28)
        else:
            race.vsc_active = True
            race.vsc_timer = random.uniform(8, 18)
        return True

    return False

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
        
        # Track display
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
        self.yellow_flag_active = False
        self.yellow_flag_timer = 0.0

        self.selected_driver = None

        # Time control
        self.time_scale = 1
        self.time_modes = [1, 2, 4, 20]
        self.time_index = 0
        self.paused = False

        self._load_race()
        
        # UI Buttons
        self.speed_buttons = []
        self.pause_button = None
        self.pit_button = None
        self.push_button = None
        self.neutral_button = None
        self.save_button = None
        self.next_race_button = None
        
        self.race_finished = False

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
        
        track_mapping = {
            "Australian GP": "Australia", "Chinese GP": "China", "Japanese GP": "Japan",
            "Bahrain GP": "Bahrain", "Saudi Arabian GP": "Saudi Arabia", "Miami GP": "Miami",
            "Emilia Romagna GP": "Imola", "Monaco GP": "Monaco", "Spanish GP": "Spain",
            "Canadian GP": "Canada", "Austrian GP": "Austria", "British GP": "Silverstone",
            "Belgian GP": "Belgium", "Hungarian GP": "Hungary", "Dutch GP": "Netherlands",
            "Italian GP": "Monza", "Azerbaijan GP": "Azerbaijan", "Singapore GP": "Singapore",
            "United States GP": "USA", "Mexico City GP": "Mexico", "São Paulo GP": "Brazil",
            "Las Vegas GP": "Las Vegas", "Qatar GP": "Qatar", "Abu Dhabi GP": "Abu Dhabi",
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
        
        self.current_track = found_track
        if not self.current_track:
            print("CHYBA: Žádná trať nenalezena!")
            return
        
        self.scale_x = self.track_display_width / self.track_source_width
        self.scale_y = self.track_display_height / self.track_source_height
        
        try:
            self.track_image = pygame.image.load(self.current_track["map"])
            self.track_image = pygame.transform.scale(self.track_image, (self.track_display_width, self.track_display_height))
            print(f"✓ Mapa načtena: {self.current_track['name']}")
        except Exception as e:
            print(f"Nelze načíst mapu: {e}")
            self.track_image = None
        
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
            driver.last_pit_lap = -10
            driver.current_stint_laps = 0
            driver.tire = "MEDIUM"
            driver.next_tire = "MEDIUM"
            driver.total_time = 0.0
            driver.race_points = 0
            driver.drs_active = False
            driver.strategy_aggression = random.uniform(0.75, 1.35)
            driver.planned_stops = 2 if random.random() < 0.7 else 1

            driver.fuel = 1.0
            driver.engine_damage = 0.0
            driver.is_dnf = False
            driver.dnf_reason = None
            driver.reliability = random.uniform(0.82, 0.98)
            driver.incident_cooldown = 0

            ai_plan_stint(driver, self, is_first_stint=True)
        
        self.race_time = 0.0
        self.race_finished = False
        self.current_weather = "SUN"
        self.safety_car_active = False
        self.vsc_active = False
        self.yellow_flag_active = False
        self.championship_round += 1
        print(f"→ Kolo {self.championship_round}: {self.current_track['name']}")

    def finish_race(self):
        if self.race_finished:
            return
        self.race_finished = True
        
        finished_drivers = [d for d in self.drivers if d.finished or d.is_dnf]
        finished_drivers.sort(key=lambda d: d.total_time if d.total_time > 0 else 999999)
        
        for i, driver in enumerate(finished_drivers):
            if i < len(POINTS):
                pts = POINTS[i]
                driver.race_points = pts
                driver.points += pts
                print(f"✓ {i+1}. {driver.name} +{pts} bodů")
        
        for team in self.teams.values():
            team.update_points()

    def next_race(self):
        self.current_race_index += 1
        if self.current_race_index >= len(CALENDAR_2025):
            print("Sezóna skončila!")
            return False
        self._load_race()
        return True

    def update(self, delta_time):
        if self.paused or not self.current_track or self.race_finished:
            return
        
        delta_time *= self.time_scale
        self.race_time += delta_time

        # Počasí
        self.weather_timer += delta_time
        if self.weather_timer > WEATHER_CHANGE_TIME * 1.5:
            self.weather_timer = 0
            roll = random.random()
            if roll < 0.65: self.current_weather = "SUN"
            elif roll < 0.88: self.current_weather = "CLOUD"
            else: self.current_weather = "RAIN"

        # Safety car
        if random.random() < 0.0008 and not self.safety_car_active:
            self.safety_car_active = True
            self.safety_car_timer = random.uniform(10, 28)

        if self.safety_car_active:
            self.safety_car_timer -= delta_time
            if self.safety_car_timer <= 0:
                self.safety_car_active = False

        if self.vsc_active:
            self.vsc_timer -= delta_time
            if self.vsc_timer <= 0:
                self.vsc_active = False

        if self.yellow_flag_active:
            self.yellow_flag_timer += delta_time
            if self.yellow_flag_timer > 6:
                self.yellow_flag_active = False
                self.yellow_flag_timer = 0

        path = self.current_track["racing_line"]
        path_len = len(path)
        race_progress = max((d.current_lap for d in self.drivers if not d.finished), default=0) / self.current_track["laps"]

        for driver in self.drivers:
            if driver.finished or driver.is_dnf:
                continue

            driver.ai_decision_timer += delta_time

            if random.random() < 0.012 and not driver.is_dnf:
                generate_incident(driver, self)

            if driver != self.selected_driver and driver.ai_decision_timer > 1.6:
                driver.pace_mode = ai_choose_pace(driver, race_progress, self.current_weather)
                
                if ai_should_pit(driver, self):
                    driver.pit_requested = True
                    driver.last_pit_lap = driver.current_lap
                
                if driver.in_pit and driver.pit_timer > PIT_TIME - 0.1:
                    ai_plan_stint(driver, self, is_first_stint=False)
                
                driver.ai_decision_timer = 0

            # Výpočet rychlosti
            tire_bonus = TIRES.get(driver.tire, TIRES["MEDIUM"])["pace"]
            pace_bonus = PACE.get(driver.pace_mode, PACE["NEUTRAL"])["pace"]
            wear_penalty = driver.tire_wear * 0.55
            weather_mod = WEATHER_TYPES.get(self.current_weather, WEATHER_TYPES["SUN"])["lap_modifier"]

            target_lap_time = driver.base_lap_time + tire_bonus + pace_bonus
            target_lap_time *= (1 + wear_penalty + weather_mod)
            if target_lap_time < 1: target_lap_time = 1.0

            segments_per_sec = path_len / target_lap_time
            speed = segments_per_sec

            if driver.drs_active and self.current_weather != "RAIN":
                speed *= 1.13
            if driver.in_pit or driver.on_pit_lane:
                speed *= 0.32
            if self.safety_car_active:
                speed *= 0.52

            driver.progress += speed * delta_time

            while driver.progress >= 1.0:
                driver.progress -= 1.0
                driver.track_index = (driver.track_index + 1) % path_len
                
                if driver.track_index == 0:
                    driver.current_lap += 1
                    driver.total_time = self.race_time
                    if driver.current_lap >= self.current_track["laps"]:
                        driver.finished = True

            wear_rate = PACE[driver.pace_mode]["wear"] * TIRES[driver.tire]["wear"]
            driver.tire_wear += delta_time * wear_rate * 0.018
            driver.tire_wear = min(1.0, driver.tire_wear)

            if driver.in_pit:
                driver.pit_timer += delta_time
                if driver.pit_timer >= PIT_TIME:
                    driver.in_pit = False
                    driver.tire = driver.next_tire
                    driver.tire_wear = 0.0
                    driver.pit_requested = False
                    driver.last_pit_lap = driver.current_lap
                    driver.track_index = (driver.track_index + 6) % path_len
                    driver.progress = 0.0

        self.update_drs()
        self.handle_battles()

        if all(d.finished or d.is_dnf for d in self.drivers):
            self.finish_race()

    def update_drs(self):
        ordered = sorted(self.drivers, key=lambda d: (d.current_lap, d.distance), reverse=True)
        for i, driver in enumerate(ordered):
            driver.drs_active = False
            if i == 0: continue
            front = ordered[i - 1]
            gap = front.distance - driver.distance
            if gap < 25 and self.current_weather != "RAIN" and self.race_time > 5:
                driver.drs_active = True

    def handle_battles(self):
        path_len = len(self.current_track["racing_line"])
        ordered = sorted(self.drivers, key=lambda d: d.current_lap * path_len + d.track_index + d.progress, reverse=True)
        
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
                    print(f"⚡ {behind.name} předjel {front.name}")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_screen(GAME_STATE_MENU)
                if event.key == pygame.K_TAB:
                    self.time_index = (self.time_index + 1) % len(self.time_modes)
                    self.time_scale = self.time_modes[self.time_index]
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                for rect, driver in self.driver_rects:
                    if rect.collidepoint(mouse_pos):
                        self.selected_driver = driver
                
                if self.pit_button and self.pit_button.collidepoint(mouse_pos) and self.selected_driver:
                    self.selected_driver.pit_requested = True
                    self.selected_driver.next_tire = self.selected_driver.tire
                
                if self.push_button and self.push_button.collidepoint(mouse_pos) and self.selected_driver:
                    self.selected_driver.pace_mode = "PUSH"
                if self.neutral_button and self.neutral_button.collidepoint(mouse_pos) and self.selected_driver:
                    self.selected_driver.pace_mode = "NEUTRAL"
                if self.save_button and self.save_button.collidepoint(mouse_pos) and self.selected_driver:
                    self.selected_driver.pace_mode = "SAVE"
                
                if self.race_finished and self.next_race_button and self.next_race_button.collidepoint(mouse_pos):
                    self.next_race()
                
                for button in self.speed_buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self.time_scale = button["speed"]
                
                if self.pause_button and self.pause_button.collidepoint(mouse_pos):
                    self.paused = not self.paused

    def draw(self, screen):
        screen.fill((0, 100, 0))
        
        # === LEVÝ PANEL - INFO + LEADERBOARD ===
        current_lap = max((d.current_lap for d in self.drivers), default=0)
        lap_text = self.font_big.render(f"Kolo {current_lap}/{self.current_track['laps']}", True, (255, 255, 100))
        screen.blit(lap_text, (30, 25))

        time_text = self.font.render(f"Čas: {self.race_time:.1f}s", True, (255, 255, 255))
        screen.blit(time_text, (30, 65))

        speed_text = self.font.render(f"Rychlost: {self.time_scale}x", True, (255, 255, 255))
        screen.blit(speed_text, (30, 90))

        weather_text = self.font.render(f"Počasí: {self.current_weather}", True, (255, 255, 0))
        screen.blit(weather_text, (30, 115))

        # Vlajky
        if self.safety_car_active:
            sc = self.font.render("🚨 SAFETY CAR", True, (255, 80, 0))
            screen.blit(sc, (380, 25))
        elif self.vsc_active:
            vsc = self.font.render("🚧 VSC", True, (255, 200, 0))
            screen.blit(vsc, (380, 25))
        elif self.yellow_flag_active:
            yf = self.font.render("🟡 ŽLUTÁ VLÁJKA", True, (255, 255, 0))
            screen.blit(yf, (380, 25))

        # Leaderboard
        y = 170
        self.driver_rects = []
        ordered = sorted(self.drivers, key=lambda d: 
            (d.current_lap * 10000 + d.track_index * 100 + d.progress * 100), reverse=True)
        
        leader_lap = ordered[0].current_lap if ordered else 0
        leader_prog = ordered[0].track_index + ordered[0].progress if ordered else 0
        
        for i, driver in enumerate(ordered[:20]):
            rect = pygame.Rect(30, y, 460, 32)
            self.driver_rects.append((rect, driver))
            
            if driver == self.selected_driver:
                pygame.draw.rect(screen, (70, 70, 90), rect)
            
            if driver.is_dnf:
                gap_str = f"DNF ({driver.dnf_reason})"
                color = (200, 60, 60)
            elif driver.finished:
                gap_str = f"({driver.total_time:.1f}s)"
                color = (180, 180, 180)
            elif driver.current_lap == leader_lap:
                gap_raw = (leader_prog - (driver.track_index + driver.progress)) * (85 / len(self.current_track["racing_line"]))
                gap_str = f"+{gap_raw:.1f}s"
                color = self.teams.get(driver.team_name, (255,255,255)).color
            else:
                laps_down = leader_lap - driver.current_lap
                gap_str = f"+{laps_down} kolo" if laps_down == 1 else f"+{laps_down} kol"
                color = self.teams.get(driver.team_name, (255,255,255)).color

            drs = " DRS" if driver.drs_active else ""
            text = self.font.render(f"P{i+1} {driver.name}{drs} | {gap_str}", True, color)
            screen.blit(text, (38, y + 6))
            y += 36

        # === MAPA ===
        map_x = 520
        map_y = 80
        map_w = 680
        map_h = 440
        
        if self.track_image:
            scaled_map = pygame.transform.scale(self.track_image, (map_w, map_h))
            screen.blit(scaled_map, (map_x, map_y))
            
            scale_x = map_w / self.track_source_width
            scale_y = map_h / self.track_source_height
            path = self.current_track["racing_line"]
            
            # DRS zóny
            for start, end in self.current_track.get("drs_zones", []):
                for i in range(start, min(end, len(path)-1)):
                    x1 = path[i][0] * scale_x + map_x
                    y1 = path[i][1] * scale_y + map_y
                    x2 = path[i+1][0] * scale_x + map_x
                    y2 = path[i+1][1] * scale_y + map_y
                    pygame.draw.line(screen, (0, 220, 255), (int(x1), int(y1)), (int(x2), int(y2)), 5)
            
            # Pit lane
            if "pit_lane" in self.current_track:
                scaled_pit = [(p[0]*scale_x + map_x, p[1]*scale_y + map_y) for p in self.current_track["pit_lane"]]
                if len(scaled_pit) > 1:
                    pygame.draw.lines(screen, (255, 140, 0), False, scaled_pit, 4)
            
            # Auta na trati
            for driver in self.drivers:
                if driver.is_dnf: continue
                i = driver.track_index
                next_i = (i + 1) % len(path)
                x1, y1 = path[i]
                x2, y2 = path[next_i]
                x = x1 * scale_x + (x2 - x1) * driver.progress * scale_x + map_x
                y = y1 * scale_y + (y2 - y1) * driver.progress * scale_y + map_y
                
                color = self.teams[driver.team_name].color
                size = 10 if driver == self.selected_driver else 7
                pygame.draw.circle(screen, (255,255,255), (int(x), int(y)), size + 2)
                pygame.draw.circle(screen, color, (int(x), int(y)), size)

        # === TLAČÍTKA (PAUSE + RYCHLOST) ===
        btn_y = 545
        btn_width = 85
        btn_height = 50
        start_x = 620
        
        # Pause
        self.pause_button = pygame.Rect(start_x, btn_y, btn_width, btn_height)
        pause_color = (255, 100, 100) if self.paused else (100, 100, 100)
        pygame.draw.rect(screen, pause_color, self.pause_button)
        screen.blit(self.font.render("PAUSE", True, (255,255,255)), 
                    self.font.render("PAUSE", True, (255,255,255)).get_rect(center=self.pause_button.center))

        # Speed buttons
        self.speed_buttons = []
        speeds = [1, 2, 4, 20]
        texts = ["1x", "2x", "4x", "20x"]
        for i, spd in enumerate(speeds):
            rect = pygame.Rect(start_x + 100 + i * 110, btn_y, btn_width, btn_height)
            color = (200, 200, 0) if spd == self.time_scale else (70, 70, 80)
            pygame.draw.rect(screen, color, rect)
            txt = self.font.render(texts[i], True, (255,255,255))
            screen.blit(txt, txt.get_rect(center=rect.center))
            self.speed_buttons.append({"rect": rect, "speed": spd})

        # === PRAVÝ PANEL - STANDINGS ===
        right_x = 1650
        
        title1 = self.font_big.render("CHAMPIONSHIP STANDINGS", True, (255, 255, 0))
        screen.blit(title1, (right_x - 210, 20))
        
        y = 65
        for i, team in enumerate(sorted(self.teams.values(), key=lambda t: t.points, reverse=True)[:10]):
            txt = self.font.render(f"{i+1}. {team.name}: {team.points} pts", True, team.color)
            screen.blit(txt, (right_x - 210, y))
            y += 28

        title2 = self.font_big.render("DRIVERS STANDINGS", True, (255, 220, 100))
        screen.blit(title2, (right_x - 190, y + 25))
        
        y += 60
        sorted_drivers = sorted(self.drivers, key=lambda d: d.points, reverse=True)
        for i, driver in enumerate(sorted_drivers[:20]):
            color = self.teams.get(driver.team_name, (200,200,200)).color
            txt = self.font.render(f"{i+1}. {driver.name} — {driver.points} pts", True, color)
            screen.blit(txt, (right_x - 210, y))
            y += 26

        # === OVERLAY "ZÁVOD SKONČIL" + TLAČÍTKO DALŠÍ ZÁVOD ===
        if self.race_finished:
            overlay = pygame.Rect(520, 340, 680, 220)
            pygame.draw.rect(screen, (20, 20, 30), overlay)
            pygame.draw.rect(screen, (255, 215, 0), overlay, 5)

            finish_title = self.font_big.render("ZÁVOD SKONČIL", True, (255, 215, 0))
            screen.blit(finish_title, (finish_title.get_rect(centerx=860, centery=400).topleft))

            # Tlačítko "Další závod"
            self.next_race_button = pygame.Rect(680, 480, 340, 60)
            pygame.draw.rect(screen, (80, 200, 100), self.next_race_button)
            next_text = self.font.render("DALŠÍ ZÁVOD →", True, (255, 255, 255))
            screen.blit(next_text, next_text.get_rect(center=self.next_race_button.center))

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
