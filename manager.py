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

#Ai si vybíra kola
def ai_choose_tire(driver, current_weather):
    """AI si vybírá gumy s velkým vlivem počasí"""
    if current_weather == "RAIN":
        if random.random() < 0.95:          # 95% šance na mokré gumy v dešti
            return "WET" if random.random() < 0.6 else "INTER"
        else:
            return "INTER"                  # malá šance na chybu

    elif current_weather == "CLOUD":
        if random.random() < 0.75:
            return "INTER"
        else:
            return "MEDIUM"

    # Sucho (SUN)
    else:
        if random.random() < 0.92:          # velmi malá šance na mokré gumy za sucha
            return "HARD" if driver.current_lap > 25 else "MEDIUM" if driver.current_lap > 10 else "SOFT"
        else:
            return "MEDIUM"                 # výjimečná chyba

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
    """NOVÁ verze s undercut/overcut logikou - hráčovi jezdci neboxují sami"""
    
    # Hráčovi jezdci (z jeho týmu) nikdy neboxují sami od sebe
    if race.player_team and driver.team_name == race.player_team.name:
        return False

    if driver.in_pit or driver.on_pit_lane:
        return False
    if driver.current_lap - driver.last_pit_lap < 6:
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
        self.font = pygame.font.SysFont("arial", 24)
        self.font_big = pygame.font.SysFont("arial", 32)
        self.font_small = pygame.font.SysFont("arial", 18)

        # === STAVY OBRAZOVKY ===
        self.state = "TEAM_SELECT"          # "TEAM_SELECT" → "SEASON_START" → "RACE"
        self.player_team = None

        # Mapa
        self.track_display_width = 720
        self.track_display_height = 440
        self.track_source_width = 1000      # ← přidáno
        self.track_source_height = 1000     # ← přidáno
        self.track_image = None
        self.current_track = None

        # Championship data
        self.current_race_index = 0
        self.championship_round = 0
        self.teams = {}
        self.drivers = []

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
        self.time_scale = 1
        self.paused = False
        self.race_finished = False

        self.driver_rects = []
        self.speed_buttons = []
        self.pause_button = None
        self.pit_button1 = None
        self.pit_button2 = None
        self.start_season_button = None

        self.show_tire_select = False
        self.tire_select_for = None
        self.tire_select_buttons = []

        self._initialize_championship()

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

        track_name = track_mapping.get(race_name)
        self.current_track = next((t for t in tracks if t["name"] == track_name), None)
        if not self.current_track and tracks:
            self.current_track = tracks[self.current_race_index % len(tracks)]

        if not self.current_track:
            print("CHYBA: Trať nenalezena!")
            return

        try:
            self.track_image = pygame.image.load(self.current_track["map"])
            self.track_image = pygame.transform.scale(self.track_image, 
                (self.track_display_width, self.track_display_height))
            print(f"✓ Načtena trať: {self.current_track['name']}")
        except Exception as e:
            print(f"Chyba načtení mapy: {e}")
            self.track_image = None

        for driver in self.drivers:
            driver.track_index = 0
            driver.progress = 0.0
            driver.current_lap = 0
            driver.finished = False
            driver.pit_requested = False
            driver.in_pit = False
            driver.pit_timer = 0.0
            driver.tire_wear = 0.0
            driver.last_pit_lap = -10
            driver.tire = "MEDIUM"
            driver.next_tire = "MEDIUM"
            driver.total_time = 0.0
            driver.drs_active = False
            driver.strategy_aggression = random.uniform(0.75, 1.35)
            driver.planned_stops = 2 if random.random() < 0.7 else 1
            driver.is_dnf = False
            driver.dnf_reason = None
            driver.incident_cooldown = 0

            ai_plan_stint(driver, self, True)

        self.race_time = 0.0
        self.race_finished = False
        self.current_weather = "SUN"
        self.safety_car_active = False
        self.vsc_active = False
        self.yellow_flag_active = False

    def finish_race(self):
        if self.race_finished:
            return
        self.race_finished = True
        
        # Pouze jezdci, kteří skutečně dokončili závod (ne DNF)
        finished_drivers = [d for d in self.drivers if d.finished and not d.is_dnf]
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

                        # AI rozhodnutí - pouze pro jezdce, které neovládá hráč
            if (driver != self.player_team.drivers[0] and 
                driver != self.player_team.drivers[1] and 
                driver.ai_decision_timer > 1.6):

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
            driver.tire_wear += delta_time * wear_rate * 0.085   # ← zrychlené opotřebení
            driver.tire_wear = min(1.0, driver.tire_wear)

            # === PIT STOP LOGIKA ===
            if driver.pit_requested and not driver.in_pit and not driver.on_pit_lane:
                # Začátek pit stopu - jezdec zajede do pitlane
                driver.on_pit_lane = True
                driver.in_pit = True
                driver.pit_timer = 0.0
                driver.pit_requested = False
                print(f"→ {driver.name} zajíždí do boxů")

            if driver.in_pit:
                driver.pit_timer += delta_time
                
                # Po dokončení pit stopu
                if driver.pit_timer >= PIT_TIME:
                    driver.in_pit = False
                    driver.on_pit_lane = False
                    driver.tire = driver.next_tire
                    driver.tire_wear = 0.0
                    driver.last_pit_lap = driver.current_lap
                    
                    # Vrátíme jezdce zpět na trať (o několik pozic vpřed)
                    driver.track_index = (driver.track_index + 8) % path_len
                    driver.progress = 0.3   # trochu vpřed, aby nevznikaly kolize
                    
                    print(f"✓ {driver.name} dokončil pit stop → {driver.tire}")

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
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if self.state == "TEAM_SELECT":
                    for i, (team_name, team) in enumerate(self.teams.items()):
                        rect = pygame.Rect(720, 180 + i*75, 520, 70)
                        if rect.collidepoint(pos):
                            self.player_team = team
                            self.state = "SEASON_START"
                            print(f"Vybrán tým: {team_name}")
                            return

                elif self.state == "SEASON_START":
                    if self.start_season_button and self.start_season_button.collidepoint(pos):
                        self.state = "RACE"
                        self._load_race()
                        return

                elif self.state == "RACE":
                    # Klik na BOX jezdec 1 a 2
                    if self.pit_button1 and self.pit_button1.collidepoint(pos):
                        self.show_tire_select = True
                        self.tire_select_for = "driver1"
                        self.tire_select_buttons = []
                        return

                    if self.pit_button2 and self.pit_button2.collidepoint(pos):
                        self.show_tire_select = True
                        self.tire_select_for = "driver2"
                        self.tire_select_buttons = []
                        return

                    # Výběr pneumatik
                    if self.show_tire_select and self.tire_select_buttons:
                        for rect, tire_type in self.tire_select_buttons:
                            if rect.collidepoint(pos):
                                if self.tire_select_for == "driver1":
                                    self.player_team.drivers[0].next_tire = tire_type
                                    self.player_team.drivers[0].pit_requested = True
                                else:
                                    self.player_team.drivers[1].next_tire = tire_type
                                    self.player_team.drivers[1].pit_requested = True
                                self.show_tire_select = False
                                self.tire_select_buttons = []
                                print(f"Nasazeny {tire_type} pro {self.tire_select_for}")
                                return

                    # Myš na pause a speed tlačítka
                    if self.pause_button and self.pause_button.collidepoint(pos):
                        self.paused = not self.paused

                    for btn in self.speed_buttons:
                        if btn["rect"].collidepoint(pos):
                            self.time_scale = btn["speed"]

                    if self.race_finished and self.next_race_button and self.next_race_button.collidepoint(pos):
                        self.next_race()

            # ==================== KLÁVESNICOVÉ OVLÁDÁNÍ ====================
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_screen(GAME_STATE_MENU)

                # Pause
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused

                # Rychlosti času
                elif event.key == pygame.K_1:
                    self.time_scale = 1
                elif event.key == pygame.K_2:
                    self.time_scale = 2
                elif event.key == pygame.K_3:
                    self.time_scale = 4
                elif event.key == pygame.K_4:
                    self.time_scale = 20

                # Rychlé přepínání 1x ↔ 20x
                elif event.key == pygame.K_TAB:
                    self.time_scale = 20 if self.time_scale == 1 else 1

    def draw(self, screen):
        screen.fill((0, 100, 0))

        if self.state == "TEAM_SELECT":
            screen.blit(self.font_big.render("VYBERTE SVŮJ TÝM", True, (255, 215, 0)), (720, 120))
            for i, (team_name, team) in enumerate(self.teams.items()):
                rect = pygame.Rect(720, 180 + i*75, 520, 70)
                pygame.draw.rect(screen, team.color, rect)
                pygame.draw.rect(screen, (255,255,255), rect, 4)
                txt = self.font_big.render(team_name.upper(), True, (0,0,0))
                screen.blit(txt, txt.get_rect(center=rect.center))

        elif self.state == "SEASON_START":
            screen.blit(self.font_big.render(f"Váš tým: {self.player_team.name}", True, self.player_team.color), (720, 300))
            self.start_season_button = pygame.Rect(760, 480, 400, 80)
            pygame.draw.rect(screen, (0, 180, 80), self.start_season_button)
            pygame.draw.rect(screen, (255,255,255), self.start_season_button, 4)
            txt = self.font_big.render("ZAČÁTEK SEZÓNY", True, (255,255,255))
            screen.blit(txt, txt.get_rect(center=self.start_season_button.center))

        elif self.state == "RACE":
            # Horní informace
            current_lap = max((d.current_lap for d in self.drivers), default=0)
            track_name = self.current_track["name"] if self.current_track else "?"

            screen.blit(self.font_big.render(f"Kolo {current_lap}/{self.current_track['laps']}", True, (255, 255, 100)), (40, 25))
            screen.blit(self.font.render(f"Čas: {self.race_time:.1f}s", True, (255, 255, 255)), (40, 65))
            screen.blit(self.font.render(f"Počasí: {self.current_weather}", True, (255, 255, 0)), (40, 95))

            # Název trati uprostřed
            screen.blit(self.font_big.render(track_name.upper(), True, (255, 215, 0)), 
                        self.font_big.render(track_name.upper(), True, (255, 215, 0)).get_rect(centerx=960, centery=45))

            # === PODIUM (zobrazí se po skončení závodu) ===
                        # === PODIUM (pouze jezdci, kteří dokončili závod) ===
            if self.race_finished:
                finished = [d for d in self.drivers if d.finished and not d.is_dnf]
                finished.sort(key=lambda d: d.total_time if d.total_time > 0 else 999999)

                podium_y = 78

                #1. místo
                if len(finished) > 0:
                    d1 = finished[0]
                    screen.blit(self.font_big.render(f"1. {d1.name}", True, (255, 215, 0)), (780, podium_y))   # zlato

                #2. místo
                if len(finished) > 1:
                    d2 = finished[1]
                    screen.blit(self.font.render(f"2. {d2.name}", True, (192, 192, 192)), (820, podium_y + 42))  # stříbro

                #3. místo
                if len(finished) > 2:
                    d3 = finished[2]
                    screen.blit(self.font.render(f"3. {d3.name}", True, (205, 127, 50)), (820, podium_y + 72))   # bronz

            # Vlajky
            if self.safety_car_active:
                screen.blit(self.font.render("🚨 SAFETY CAR", True, (255, 80, 0)), (1250, 30))
            elif self.vsc_active:
                screen.blit(self.font.render("🚧 VSC", True, (255, 200, 0)), (1250, 30))
            elif self.yellow_flag_active:
                screen.blit(self.font.render("🟡 ŽLUTÁ VLÁJKA", True, (255, 255, 0)), (1250, 30))

                        # === LEADERBOARD VLEVO ===
            y = 170
            self.driver_rects = []

            if self.race_finished:
                # === FINÁLNÍ VÝSLEDKY PO SKONČENÍ ZÁVODU ===
                finished = [d for d in self.drivers if d.finished and not d.is_dnf]
                finished.sort(key=lambda d: d.total_time if d.total_time > 0 else 999999)

                # DNF jezdci na konec
                dnfs = [d for d in self.drivers if d.is_dnf]
                all_results = finished + dnfs

                for i, driver in enumerate(all_results):
                    rect = pygame.Rect(30, y, 460, 34)
                    self.driver_rects.append((rect, driver))

                    if driver.is_dnf:
                        position_text = f"DNF"
                        gap_str = f"({driver.dnf_reason})"
                        color = (200, 60, 60)
                    else:
                        position_text = f"{i+1}."
                        if i < 3:
                            gap_str = f"({driver.total_time:.1f}s)"
                        else:
                            gap_str = f"+{driver.total_time - finished[0].total_time:.1f}s"
                        color = self.teams.get(driver.team_name, (255,255,255)).color

                    drs = ""  # po závodě už DRS neukazujeme
                    text = self.font.render(f"{position_text} {driver.name}{drs} | {gap_str}", True, color)
                    screen.blit(text, (40, y + 7))
                    y += 38

            else:
                # === BĚŽNÝ LEADERBOARD BĚHEM ZÁVODU ===
                ordered = sorted(self.drivers, key=lambda d: d.current_lap*10000 + d.track_index*100 + d.progress*100, reverse=True)
                leader_lap = ordered[0].current_lap if ordered else 0
                leader_prog = ordered[0].track_index + ordered[0].progress if ordered else 0

                for i, driver in enumerate(ordered[:20]):
                    rect = pygame.Rect(30, y, 460, 34)
                    self.driver_rects.append((rect, driver))
                    if driver == self.selected_driver:
                        pygame.draw.rect(screen, (70, 70, 100), rect)

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
                    screen.blit(text, (40, y + 7))
                    y += 38

            # === MAPA + AUTA ===
            map_x, map_y = 480, 110
            map_w, map_h = 720, 440
            if self.track_image:
                scaled = pygame.transform.scale(self.track_image, (map_w, map_h))
                screen.blit(scaled, (map_x, map_y))

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
                    if driver.is_dnf or driver.finished: continue
                    i = driver.track_index
                    next_i = (i + 1) % len(path)
                    x1, y1 = path[i]
                    x2, y2 = path[next_i]
                    x = x1 * scale_x + (x2 - x1) * driver.progress * scale_x + map_x
                    y = y1 * scale_y + (y2 - y1) * driver.progress * scale_y + map_y

                    color = self.teams[driver.team_name].color
                    size = 11 if driver == self.selected_driver else 8
                    pygame.draw.circle(screen, (255,255,255), (int(x), int(y)), size + 3)
                    pygame.draw.circle(screen, color, (int(x), int(y)), size)

            # === BOXY PRO JEZDCE 1 A 2 (uprostřed pod speed buttons, BOX uvnitř černého boxu) ===
            box_y = 650
            box_w = 380
            box_h = 95

            # Jezdec 1 - celý černý box
            d1 = self.player_team.drivers[0]
            wear1 = int(d1.tire_wear * 100)
            box1_rect = pygame.Rect(480, box_y, box_w, box_h)
            pygame.draw.rect(screen, (30, 30, 40), box1_rect)                    # černý background
            pygame.draw.rect(screen, self.teams[d1.team_name].color, box1_rect, 4)  # barevný rámeček

            screen.blit(self.font.render(f"1. {d1.name}", True, (255,255,255)), (500, box_y + 12))
            screen.blit(self.font.render(f"Gumy: {d1.tire}", True, (255,215,0)), (500, box_y + 42))
            screen.blit(self.font_small.render(f"Opotřebení kol: {wear1}%", True, (255,180,0)), (500, box_y + 68))

            # Tlačítko BOX uvnitř černého boxu (vpravo)
            self.pit_button1 = pygame.Rect(780, box_y + 18, 75, 60)
            pygame.draw.rect(screen, (200, 60, 60), self.pit_button1)
            pygame.draw.rect(screen, (255,255,255), self.pit_button1, 3)
            screen.blit(self.font.render("BOX", True, (255,255,255)), 
                        self.font.render("BOX", True, (255,255,255)).get_rect(center=self.pit_button1.center))

            # Jezdec 2 - celý černý box
            d2 = self.player_team.drivers[1]
            wear2 = int(d2.tire_wear * 100)
            box2_rect = pygame.Rect(880, box_y, box_w, box_h)
            pygame.draw.rect(screen, (30, 30, 40), box2_rect)
            pygame.draw.rect(screen, self.teams[d2.team_name].color, box2_rect, 4)

            screen.blit(self.font.render(f"2. {d2.name}", True, (255,255,255)), (900, box_y + 12))
            screen.blit(self.font.render(f"Gumy: {d2.tire}", True, (255,215,0)), (900, box_y + 42))
            screen.blit(self.font_small.render(f"Opotřebení kol: {wear2}%", True, (255,180,0)), (900, box_y + 68))

            # Tlačítko BOX uvnitř černého boxu (vpravo)
            self.pit_button2 = pygame.Rect(1180, box_y + 18, 75, 60)
            pygame.draw.rect(screen, (200, 60, 60), self.pit_button2)
            pygame.draw.rect(screen, (255,255,255), self.pit_button2, 3)
            screen.blit(self.font.render("BOX", True, (255,255,255)), 
                        self.font.render("BOX", True, (255,255,255)).get_rect(center=self.pit_button2.center))


            # === PAUSE + SPEED BUTTONS (dole uprostřed) ===
            btn_y = 580
            btn_width = 90
            btn_height = 55
            start_x = 620

            # Pause button
            self.pause_button = pygame.Rect(start_x, btn_y, btn_width, btn_height)
            pause_color = (255, 80, 80) if self.paused else (100, 100, 100)
            pygame.draw.rect(screen, pause_color, self.pause_button)
            pause_text = self.font.render("PAUSE", True, (255, 255, 255))
            screen.blit(pause_text, pause_text.get_rect(center=self.pause_button.center))

            # Speed buttons s vizuálním zvýrazněním
            self.speed_buttons = []
            speeds = [1, 2, 4, 20]
            texts = ["1x", "2x", "4x", "20x"]
            for i, spd in enumerate(speeds):
                rect = pygame.Rect(start_x + 110 + i * 105, btn_y, btn_width, btn_height)
                
                # Zvýraznění - žlutá barva pokud je aktivní (klávesnice nebo myš)
                if spd == self.time_scale:
                    color = (255, 215, 0)      # zlatá
                    text_color = (0, 0, 0)
                else:
                    color = (70, 70, 80)
                    text_color = (255, 255, 255)
                
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 3)  # bílý rámeček
                
                txt = self.font.render(texts[i], True, text_color)
                screen.blit(txt, txt.get_rect(center=rect.center))
                
                self.speed_buttons.append({"rect": rect, "speed": spd})

            # === PRAVÝ PANEL - STANDINGS ===
            right_x = 1650
            screen.blit(self.font_big.render("CHAMPIONSHIP STANDINGS", True, (255, 255, 0)), (right_x - 240, 20))
            y = 70
            for i, team in enumerate(sorted(self.teams.values(), key=lambda t: t.points, reverse=True)[:10]):
                txt = self.font.render(f"{i+1}. {team.name}: {team.points} pts", True, team.color)
                screen.blit(txt, (right_x - 240, y))
                y += 28

            screen.blit(self.font_big.render("DRIVERS STANDINGS", True, (255, 220, 100)), (right_x - 210, y + 30))
            y += 60
            for i, driver in enumerate(sorted(self.drivers, key=lambda d: d.points, reverse=True)[:20]):
                color = self.teams.get(driver.team_name, (200,200,200)).color
                txt = self.font.render(f"{i+1}. {driver.name} — {driver.points} pts", True, color)
                screen.blit(txt, (right_x - 240, y))
                y += 26

            # === VÝBĚR PNEUMATIK (zeleně označená vybraná guma) ===
            if self.show_tire_select:
                overlay = pygame.Rect(520, 280, 480, 420)
                pygame.draw.rect(screen, (20,20,35), overlay)
                pygame.draw.rect(screen, (255,215,0), overlay, 6)
                screen.blit(self.font_big.render("VYBER PNEUMATIKY", True, (255,215,0)), (600, 310))

                tires = ["SOFT", "MEDIUM", "HARD", "INTER", "WET"]
                tire_colors = {"SOFT":(255,60,60), "MEDIUM":(255,180,0), "HARD":(220,220,220),
                               "INTER":(0,180,255), "WET":(30,80,255)}

                self.tire_select_buttons = []
                selected_tire = None
                if self.tire_select_for == "driver1":
                    selected_tire = self.player_team.drivers[0].next_tire
                elif self.tire_select_for == "driver2":
                    selected_tire = self.player_team.drivers[1].next_tire

                for i, tire in enumerate(tires):
                    btn = pygame.Rect(570, 380 + i*58, 380, 50)
                    color = tire_colors[tire]
                    border_color = (0, 255, 0) if tire == selected_tire else (255,255,255)
                    pygame.draw.rect(screen, color, btn)
                    pygame.draw.rect(screen, border_color, btn, 4)   # zelený rám pro vybranou
                    txt = self.font.render(tire, True, (0,0,0))
                    screen.blit(txt, txt.get_rect(center=btn.center))
                    self.tire_select_buttons.append((btn, tire))

            # Overlay po skončení závodu
            if self.race_finished:
                overlay = pygame.Rect(520, 340, 680, 220)
                pygame.draw.rect(screen, (20,20,30), overlay)
                pygame.draw.rect(screen, (255,215,0), overlay, 6)
                screen.blit(self.font_big.render("ZÁVOD SKONČIL", True, (255,215,0)), (650, 370))

                self.next_race_button = pygame.Rect(680, 460, 360, 70)
                pygame.draw.rect(screen, (80,200,100), self.next_race_button)
                screen.blit(self.font.render("DALŠÍ ZÁVOD →", True, (255,255,255)), 
                            self.font.render("DALŠÍ ZÁVOD →", True, (255,255,255)).get_rect(center=self.next_race_button.center))

                pass

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