import pygame
import math
import sys
import random
import json
import os
from datetime import datetime
from tracks_data import tracks
from championship_data import TEAMS, DRIVER_BASE_TIMES, CALENDAR_2025

# Adresář, kde leží manager.py - všechny relativní cesty (mapy, zvuky, uložené hry)
# se vždy počítají odsud, ne od aktuálního pracovního adresáře (ten se liší podle
# toho, odkud/čím se hra spouští - dvojklik, IDE, terminál...).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Na Windows s displejem se zvětšením (typicky 125-150 % u notebooků s 2560x1600) by
# okno jinak OS roztáhl a rozmazal a pygame by hlásil zmenšené "virtuální" rozlišení
# plochy. S DPI awareness dostane hra skutečné pixely displeje.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

pygame.init()

# === BEZPEČNÁ AUDIO INICIALIZACE (pro školní PC) ===
AUDIO_ENABLED = False
try:
    pygame.mixer.init(44100, -16, 2, 512)
    AUDIO_ENABLED = True
    print("✅ Audio inicializováno")
except pygame.error as e:
    print(f"⚠️ Audio nelze inicializovat: {e}")
    print("   Hra poběží bez zvuku (typické na školních počítačích)")
    pygame.mixer.quit()   # úplně vypnout mixer

print("Dostupné tratě:")
for track in tracks:
    print(f"  - {track['name']}")

# Globální nastavení
CURRENT_FPS = 60
IS_FULLSCREEN = False

# Globální nastavení závodu a jazyka
CURRENT_RACE_MODE = "SHORT"
CURRENT_LANGUAGE = "CS"   # CZ → CS (opraveno)

# Race phases
RACE_PHASE_FORMATION = "FORMATION"
RACE_PHASE_START = "START"
RACE_PHASE_RACING = "RACING"

# Cesty k audio komentářům
START_COMMENT_CS = os.path.join(SCRIPT_DIR, "sounds", "start_cz.mp3")
START_COMMENT_EN = os.path.join(SCRIPT_DIR, "sounds", "start_en.mp3")

# === LOKALIZACE - SNADNO ROZŠIŘITELNÁ ===
TEXTS = {
    # Hlavní menu a nastavení
    "F1 MANAGER": {"CS": "F1 MANAGER", "EN": "F1 MANAGER", "IT": "F1 MANAGER"},
    "2025 SEASON": {"CS": "2025 SEZÓNA", "EN": "2025 SEASON", "IT": "STAGIONE 2025"},
    "CHAMPIONSHIP": {"CS": "ŠAMPIONÁT", "EN": "CHAMPIONSHIP", "IT": "CAMPIONATO"},
    "PRACTICE": {"CS": "TRÉNINK", "EN": "PRACTICE", "IT": "ALLENAMENTO"},
    "SETTINGS": {"CS": "NASTAVENÍ", "EN": "SETTINGS", "IT": "IMPOSTAZIONI"},
    "VYPNOUT": {"CS": "VYPNOUT", "EN": "QUIT", "IT": "SPEGNERE"},

    # In-game menu
    "PAUSED": {"CS": "POZASTAVENO", "EN": "PAUSED", "IT": "SOSPESO"},
    "POKRAČOVAT": {"CS": "POKRAČOVAT", "EN": "CONTINUE", "IT": "CONTINUA"},
    "ULOŽIT HRU": {"CS": "ULOŽIT HRU", "EN": "SAVE GAME", "IT": "SALVA PARTITA"},
    "NAČÍST HRU": {"CS": "NAČÍST HRU", "EN": "LOAD GAME", "IT": "CARICA IL GIOCO"},
    "NASTAVENÍ": {"CS": "NASTAVENÍ", "EN": "SETTINGS", "IT": "IMPOSTAZIONI"},
    "NÁVRAT DO MENU": {"CS": "NÁVRAT DO MENU", "EN": "MAIN MENU", "IT": "TORNA AL MENU"},
    "UKONČIT HRU": {"CS": "UKONČIT HRU", "EN": "QUIT GAME", "IT": "TERMINA IL GIOCO"},

    # Závod
    "Kolo": {"CS": "Kolo", "EN": "Lap", "IT": "GIRO"},
    "Čas:": {"CS": "Čas:", "EN": "Time:", "IT": "ORA"},
    "Počasí:": {"CS": "Počasí:", "EN": "Weather:", "IT": "METEO"},
    "WEATHER_SUN": {"CS": "SLUNCE", "EN": "SUNNY", "IT": "SOLE"},
    "WEATHER_CLOUD": {"CS": "OBLAČNO", "EN": "CLOUDY", "IT": "NUVOLOSO"},
    "WEATHER_RAIN": {"CS": "DÉŠŤ", "EN": "RAIN", "IT": "PIOGGIA"},
    "Vlhkost trati:": {"CS": "Vlhkost trati:", "EN": "Track wetness:", "IT": "UMIDITÀ PISTA:"},
    "Gumy:": {"CS": "Gumy:", "EN": "Tires:", "IT": "PNEUMATICI"},
    "Opotřebení kol:": {"CS": "Opotřebení kol:", "EN": "Tire Wear:", "IT": "USURA DELLE RUOTE"},
    "FORMATION LAP": {"CS": "FORMACE KOLO", "EN": "FORMATION LAP", "IT": "GIRO DI FORMAZIONE"},
    "FLAG_SC": {"CS": "SAFETY CAR", "EN": "SAFETY CAR", "IT": "SAFETY CAR"},
    "FLAG_VSC": {"CS": "VIRTUÁLNÍ SC", "EN": "VIRTUAL SC", "IT": "SC VIRTUALE"},
    "FLAG_YELLOW": {"CS": "ŽLUTÁ VLAJKA", "EN": "YELLOW FLAG", "IT": "BANDIERA GIALLA"},
    "RACE FINISH": {"CS": "VÝSLEDKY ZÁVODU", "EN": "RACE FINISH", "IT": "ARRIVO DELLA GARA"},
    "DRIVER STANDINGS": {"CS": "POŘADÍ JEZDCŮ", "EN": "DRIVER STANDINGS", "IT": "CLASSIFICA PILOTI"},
    "TEAM STANDINGS": {"CS": "POŘADÍ TÝMŮ", "EN": "TEAM STANDINGS", "IT": "CLASSIFICA COSTRUTTORI"},
    "NEXT RACE": {"CS": "DALŠÍ ZÁVOD", "EN": "NEXT RACE", "IT": "PROSSIMA GARA"},
    "RACE FINISHED": {"CS": "ZÁVOD SKONČIL", "EN": "RACE FINISHED", "IT": "GARA TERMINATA"},
    "SEASON OVER": {"CS": "KONEC SEZÓNY", "EN": "SEASON OVER", "IT": "FINE STAGIONE"},
    "ROUND": {"CS": "Závod", "EN": "Round", "IT": "Gara"},
    "PTS": {"CS": "b.", "EN": "pts", "IT": "pt"},
    "LAP": {"CS": "kolo", "EN": "lap", "IT": "giro"},
    "LAPS": {"CS": "kol", "EN": "laps", "IT": "giri"},
    "Engine": {"CS": "Motor", "EN": "Engine", "IT": "Motore"},
    "Crash": {"CS": "Nehoda", "EN": "Crash", "IT": "Incidente"},
    "Big Shunt": {"CS": "Těžká nehoda", "EN": "Big Shunt", "IT": "Grosso incidente"},
    "Spin + Wall": {"CS": "Smyk + zeď", "EN": "Spin + Wall", "IT": "Testacoda + muro"},
    "START LIGHTS": {"CS": "STARTOVNÍ SEMAFOR", "EN": "START LIGHTS", "IT": "SEMAFORI DI PARTENZA"},
    "LIGHTS OUT...": {"CS": "SVĚTLA ZHASLA...", "EN": "LIGHTS OUT...", "IT": "LE LUCI SI SONO SPENTE..."},
    "VYBERTE SVŮJ TÝM": {"CS": "VYBERTE SVŮJ TÝM", "EN": "CHOOSE YOUR TEAM", "IT": "SCEGLI LA TUA SQUADRA"},
    "Váš tým:": {"CS": "Váš tým:", "EN": "Your team:", "IT": "Il vostro team"},
    "ZAČÁTEK SEZÓNY": {"CS": "ZAČÁTEK SEZÓNY", "EN": "START SEASON", "IT": "INIZIO DELLA STAGIONE"},

    # Nastavení
    "DÉLKA ZÁVODU": {"CS": "DÉLKA ZÁVODU", "EN": "RACE LENGTH", "IT": "DURATA DELLA GARA"},
    "SHORT RACE": {"CS": "SHORT RACE", "EN": "SHORT RACE", "IT": "GARA BREVE"},
    "FULL RACE (1h30+)": {"CS": "FULL RACE (1h30+)", "EN": "FULL RACE (1h30+)", "IT": "GARA COMPLETA (1H30+)"},
    "JAZYK": {"CS": "JAZYK", "EN": "LANGUAGE", "IT": "LINGUA"},
    "FRAMERATE (FPS)": {"CS": "FRAMERATE (FPS)", "EN": "FRAMERATE (FPS)", "IT": "FREQUENZA DEI FRAME"},
}

def format_race_time(seconds):
    """Čas závodu jako h:mm:ss.s nebo m:ss.s (stejné jednotky jako "Čas:" v hlavičce závodu)."""
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours >= 1:
        return f"{int(hours)}:{int(minutes):02d}:{secs:04.1f}"
    return f"{int(minutes)}:{secs:04.1f}"


def get_text(key, lang=None):
    if lang is None:
        lang = CURRENT_LANGUAGE
    return TEXTS.get(key, {}).get(lang, key)

WIDTH = 1920
HEIGHT = 1080

# === OKNO A ŠKÁLOVÁNÍ NA LIBOVOLNÝ DISPLEJ ===
# Celá hra se kreslí na pevné "logické" plátno WIDTH x HEIGHT (1920x1080) - všechny
# souřadnice v UI jsou pro něj. Do okna se plátno každý snímek přeškáluje (se
# zachováním poměru stran, případné okraje jsou černé) a myš se přepočítává zpátky
# na souřadnice plátna (get_mouse_pos). Díky tomu hra sedí na displeji 1366x768,
# 1920x1080, 2560x1600, 3840x2160... a okno jde libovolně zvětšovat/zmenšovat.
def get_desktop_size():
    try:
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            return sizes[0]
    except Exception:
        pass
    info = pygame.display.Info()
    return info.current_w, info.current_h


def fit_window_size(desktop_w, desktop_h):
    """Největší okno v poměru 16:9, které se vejde na plochu i s titulkem a hlavním panelem."""
    scale = min(desktop_w * 0.95 / WIDTH, desktop_h * 0.88 / HEIGHT)
    return max(640, int(WIDTH * scale)), max(360, int(HEIGHT * scale))


def apply_display_mode():
    """Vytvoří okno podle IS_FULLSCREEN (celá obrazovka v nativním rozlišení / okno na míru)."""
    desktop = get_desktop_size()
    if IS_FULLSCREEN:
        pygame.display.set_mode(desktop, pygame.FULLSCREEN)
    else:
        pygame.display.set_mode(fit_window_size(*desktop), pygame.RESIZABLE)


def toggle_fullscreen():
    global IS_FULLSCREEN
    IS_FULLSCREEN = not IS_FULLSCREEN
    apply_display_mode()


apply_display_mode()
pygame.display.set_caption("F1 manažer")

canvas = pygame.Surface((WIDTH, HEIGHT)).convert()
screen = canvas  # všechny screeny kreslí sem, do okna se to přenáší v present_frame()
view_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)  # kam v okně leží plátno
_scaled_buffer = None


def present_frame():
    """Přeškáluje plátno do okna (letterbox) a zobrazí ho."""
    global view_rect, _scaled_buffer
    window = pygame.display.get_surface()
    win_w, win_h = window.get_size()
    scale = min(win_w / WIDTH, win_h / HEIGHT)
    target_w, target_h = max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale))
    view_rect = pygame.Rect((win_w - target_w) // 2, (win_h - target_h) // 2, target_w, target_h)

    if (target_w, target_h) != (win_w, win_h):
        window.fill((0, 0, 0))
    if (target_w, target_h) == (WIDTH, HEIGHT):
        window.blit(canvas, view_rect.topleft)
    else:
        if _scaled_buffer is None or _scaled_buffer.get_size() != (target_w, target_h):
            _scaled_buffer = pygame.Surface((target_w, target_h)).convert()
        pygame.transform.smoothscale(canvas, (target_w, target_h), _scaled_buffer)
        window.blit(_scaled_buffer, view_rect.topleft)
    pygame.display.flip()


def get_mouse_pos():
    """Pozice myši v souřadnicích logického plátna (1920x1080), ne okna."""
    mouse_x, mouse_y = pygame.mouse.get_pos()
    return (int((mouse_x - view_rect.x) * WIDTH / view_rect.w),
            int((mouse_y - view_rect.y) * HEIGHT / view_rect.h))


clock = pygame.time.Clock()

GAME_STATE_MENU = "MENU"
GAME_STATE_PRACTICE = "PRACTICE"
GAME_STATE_SETTINGS = "SETTINGS"
GAME_STATE_RACE = "RACE"
game_state = GAME_STATE_MENU
current_screen = None

WEATHER_CHANGE_LAPS = 4  # jak často (v odjetých kolech lídra) se losuje nové počasí

TIRES = {
    "SOFT": {"pace": -0.3, "wear": 0.04},
    "MEDIUM": {"pace": 0.0, "wear": 0.025},
    "HARD": {"pace": 0.3, "wear": 0.015},
    "INTER": {"pace": 0.6, "wear": 0.02},
    "WET": {"pace": 1.0, "wear": 0.018},
}

# Opotřebení za JEDNO dojeté kolo při NEUTRAL tempu (viz update() - škáluje se
# skutečně ujetou vzdáleností, ne uplynulým časem, takže je stejné na všech tratích
# i při libovolném time_scale/time_compression). Hodnoty jsou kalibrované tak, aby
# guma dosáhla 100 % opotřebení zhruba v 1.4× průměrné délky stintu, kterou plánuje
# ai_plan_stint() (SOFT ~9.5, MEDIUM ~14, HARD ~21, INTER ~8, WET ~7 kol) - takže
# se běžně piťuje podle plánu (target_stint_end) a práh tire_wear > 0.88 slouží jen
# jako nouzová pojistka při agresivním tempu (PUSH) nebo prodlužovaném stintu.
TIRE_WEAR_PER_LAP = {
    "SOFT": 0.075,
    "MEDIUM": 0.051,
    "HARD": 0.034,
    "INTER": 0.089,
    "WET": 0.102,
}

POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

# === POČASÍ A VLHKOST TRATĚ ===
# Počasí (SUN / CLOUD / RAIN) se mění každých WEATHER_CHANGE_LAPS kol podle tabulky
# přechodů - déšť nepřichází z čistého nebe (SUN -> CLOUD -> RAIN a zpátky). Hlavně ale
# počasí řídí VLHKOST TRATĚ (0-1): v dešti stoupá, jinak postupně schne (pod sluncem
# rychleji než pod mrakem). Tempo, opotřebení i volba pneumatik závisí na vlhkosti
# trati, ne na okamžitém počasí - takže po dešti chvíli zůstane mokro a tým musí
# načasovat přezutí na inter/wet a zpět na slick.
WEATHER_TRANSITIONS = {
    "SUN":   (("SUN", 0.85), ("CLOUD", 0.14), ("RAIN", 0.01)),
    "CLOUD": (("SUN", 0.35), ("CLOUD", 0.53), ("RAIN", 0.12)),
    "RAIN":  (("SUN", 0.10), ("CLOUD", 0.45), ("RAIN", 0.45)),
}
WETTING_LAPS = 3.0                                     # za kolik kol v dešti trať úplně promokne
DRYING_LAPS = {"SUN": 5.0, "CLOUD": 9.0}               # za kolik kol uschne z plné vlhkosti (RAIN nesuší)
DRY_TIRES = ("SOFT", "MEDIUM", "HARD")
# Přilnavost gumy podle vlhkosti trati: (vlhkost s nejlepší přilnavostí, maximum, strmost poklesu)
TIRE_GRIP_PROFILE = {
    "SOFT":   (0.0, 1.0, 0.60),
    "MEDIUM": (0.0, 1.0, 0.58),
    "HARD":   (0.0, 1.0, 0.55),
    "INTER":  (0.5, 1.0, 0.40),
    "WET":    (1.0, 1.0, 0.28),
}
DRS_MAX_WETNESS = 0.25       # při větší vlhkosti trati je DRS zakázané
# Prahy, při kterých se AI přezouvá (k vlhkosti se přičítá osobní driver.weather_bias,
# takže neridí všichni ve stejný okamžik). Mezi "nahoru" a "dolů" je záměrně mezera
# (hystereze), aby se auta nepřezouvala sem a tam.
AI_INTER_WETNESS = 0.30      # od téhle vlhkosti inter místo slicku
AI_WET_TIRE_WETNESS = 0.78   # od téhle vlhkosti wet místo interu
AI_INTER_TO_DRY = 0.15       # pod touhle vlhkostí (a mimo déšť) zpět na slick
AI_WET_TO_INTER = 0.50       # pod touhle vlhkostí z wet zpět na inter


def tire_grip(tire, wetness):
    """Násobek rychlosti podle toho, jak se guma hodí na aktuální vlhkost trati."""
    optimum, peak, steepness = TIRE_GRIP_PROFILE[tire]
    return max(0.3, peak - steepness * (wetness - optimum) ** 2)


def tire_wear_weather_factor(tire, wetness):
    """Inter/wet na sušší trati se ničí mnohem rychleji (přehřívají se); slicky ne."""
    if tire in DRY_TIRES:
        return 1.0
    return 1.0 + 2.5 * max(0.0, TIRE_GRIP_PROFILE[tire][0] - wetness)


def next_weather(current):
    names, weights = zip(*WEATHER_TRANSITIONS[current])
    return random.choices(names, weights=weights)[0]

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

        self.drs_active = False

        self.track_index = 0
        self.progress = 0
        self.angle = 0
        self.finished = False

        self.grid_position = 0            # pořadí na startovním roštu (0 = pole position)
        self.formation_start_delay = 0.0  # kdy (race_time) se auto rozjede z roštu

        self.pit_requested = False
        self.on_pit_lane = False
        self.pit_phase = None       # None / "ENTRY" (jede k boxu) / "SERVICE" (stojí v boxu) / "EXIT"
        self.pit_box_d = 0.0        # kde v boxové uličce (v bodech racing_line od vjezdu) je box týmu

                # === NOVÉ STRATEGIE ===
        self.current_stint_laps = 0          # kolik kol už jel na těchto gumách
        self.target_stint_end = 0            # na kterém kole plánuje pit
        self.strategy_aggression = random.uniform(0.75, 1.35)  # <1 = konzervativní, >1 = agresivní
        self.weather_bias = random.uniform(-0.06, 0.08)        # o kolik dřív/později než ostatní reaguje na změnu vlhkosti
        self.planned_stops = random.choice([1, 2])            # 1-stop nebo 2-stop
        self.undercut_chance = 0.0

                # === NOVÉ: PORUCHY A DNF ===
        self.fuel = 1.0                     # 100 %
        self.reliability = random.uniform(0.82, 0.98)   # jak spolehlivé auto
        self.engine_damage = 0.0
        self.is_dnf = False
        self.dnf_reason = None              # "Engine", "Fuel", "Crash", "Spin"
        self.incident_cooldown = 0

def get_speed(driver, race):
    """Vrátí rychlost jezdce s ohledem na Safety Car a formační kolo"""
    if race.safety_car_active and not driver.in_pit:
        # Auta mimo pit jedou pod SC rychlostí danou frontou za safety carem
        # (viz ChampionshipScreen.update_safety_car / get_safety_car_speed)
        return race.get_safety_car_speed(driver)

    if driver.pit_phase == "SERVICE":
        return 0.0  # stojí u svého boxu (výměna pneumatik)

    if race.race_phase == RACE_PHASE_START and not driver.in_pit:
        # Startovní semafor: auta stojí na roštu, dokud světla nezhasnou.
        return 0.0

    if race.race_phase == RACE_PHASE_FORMATION and not driver.in_pit:
        # Formační kolo: auto se rozjede až ve svém pořadí na roštu a jede
        # stejnou pevnou rychlostí jako ostatní - pořadí se tak nikdy nezamíchá.
        if race.race_time < driver.formation_start_delay:
            return 0.0
        # Rychlost se dopočítává tak, aby CELÉ formační kolo trvalo tolik, kolik
        # trvá na reálném okruhu (formation_lap_duration - z reálné délky okruhu).
        # Počet bodů v racing_line je jen "rozlišení" ručního vykreslení tratě a
        # není úměrný reálné délce okruhu, proto se z něj čas nedá odvodit.
        path_len = len(race.current_track["racing_line"])
        pace = path_len / formation_lap_duration(race.current_track)
        # O pár řádků výš v update() se `speed *= time_compression` - to by jinak
        # znamenalo, že SHORT/FULL mód mění i délku formačního kola. Formační kolo
        # má trvat vždy stejně dlouho v reálném čase bez ohledu na zvolený režim
        # závodu, proto se tu dělení time_compression předem "vyruší".
        return pace / getattr(race, 'time_compression', 1.0)

    speed = driver.base_speed
    speed *= (1 - driver.tire_wear * 0.4)

    speed *= tire_grip(driver.tire, race.track_wetness)

    if driver.in_pit:
        speed *= 0.4

    if driver.drs_active and not race.safety_car_active:
        speed *= 1.15

    return speed

# === PIT STOPY ===
# Auto po žádosti o pit (hráč tlačítkem BOX, AI strategií) dojede k vjezdu do boxové
# uličky, projede ji sníženou rychlostí (viz get_speed: in_pit = 0.4x), ZASTAVÍ u boxu
# svého týmu na PIT_TIME (v "komprimovaných" sekundách, tj. při SHORT módu se dělí
# time_compression - stejný podíl kola v obou režimech), vymění gumy a odjede zpět na trať.
PIT_TIME = 5.0
PIT_LANE_LENGTH_M = 400.0    # reálná délka boxové uličky - z ní se dopočítá počet bodů racing_line
PIT_LANE_OFFSET_PX = 28.0    # o kolik pixelů (zdrojové souřadnice mapy) je ulička vedle trati
PIT_LANE_BLEND = 0.6         # na kolika bodech trati se auto odklání do uličky / vrací zpět
PIT_ENTRY_WINDOW = 0.6       # v jaké vzdálenosti za vjezdem se ještě dá do uličky zatočit

# === FORMAČNÍ KOLO – pevné pořadí podle roštu, žádné předjíždění ===
# Délka formačního kola = reálná délka okruhu / průměrná rychlost formace. Reálné
# délky okruhů (km) jsou z Wikipedie (seznam okruhů F1 sezóny 2025). Konkrétní časy
# formačního kola pro jednotlivé okruhy nikde veřejně zveřejněné nejsou, ale zdroje
# uvádějí formační tempo 50-120 km/h; 120 km/h navíc sedí s uživatelovým údajem pro
# Zandvoort (4,259 km -> 2:08, uživatel uvádí 1:45-2:15) i s jeho požadavkem 2-3 min
# pro Austrálii (5,278 km -> 2:38).
FORMATION_SPEED_KMH = 120.0
TRACK_LENGTH_KM = {
    "Australia": 5.278, "China": 5.451, "Japan": 5.807, "Bahrain": 5.412,
    "Saudi Arabia": 6.174, "Miami": 5.410, "Imola": 4.909, "Monaco": 3.337,
    "Canada": 4.361, "Spain": 4.657, "Austria": 4.318, "Silverstone": 5.891,
    "Hungary": 4.381, "Belgium": 7.004, "Netherlands": 4.259, "Monza": 5.793,
    "Azerbaijan": 6.003, "Singapore": 4.940, "USA": 5.513, "Mexico": 4.304,
    "Brazil": 4.309, "Las Vegas": 6.201, "Qatar": 5.419, "Abu Dhabi": 5.281,
}
FORMATION_LAP_DURATION_FALLBACK = 125.0  # pro trať, která není v TRACK_LENGTH_KM


def formation_lap_duration(track):
    """Reálná délka formačního kola dané tratě v sekundách."""
    length_km = TRACK_LENGTH_KM.get(track.get("name"))
    if length_km is None:
        return FORMATION_LAP_DURATION_FALLBACK
    return length_km / FORMATION_SPEED_KMH * 3600.0


FORMATION_GRID_GAP = 0.5     # o kolik race_time sekund později se rozjede každé další auto na roštu


_pit_geometry_cache = {}


def get_pit_geometry(track):
    """Geometrie boxové uličky: vjezd (index racing_line), délka v bodech a strana trati.

    Ulička se odvozuje z racing_line (běží podél ní od vjezdu o `length` bodů, s bočním
    odsazením), protože ručně nakreslená polyline `pit_lane` v tracks_data.py u
    zhruba třetiny tratí vůbec nenavazuje na racing_line (stovky pixelů vedle). Data z
    `pit_lane` se používají jen jako nápověda pro místo vjezdu a stranu, pokud sedí.
    """
    name = track.get("name")
    if name in _pit_geometry_cache:
        return _pit_geometry_cache[name]

    rl = track["racing_line"]
    n = len(rl)
    step_m = TRACK_LENGTH_KM.get(name, 5.0) * 1000.0 / n
    length = max(2, min(12, round(PIT_LANE_LENGTH_M / step_m)))
    entry = (n - 2) % n
    side = 1

    hint = track.get("pit_lane")
    if hint:
        px, py = hint[0]
        dists = [math.hypot(px - q[0], py - q[1]) for q in rl]
        i = min(range(n), key=lambda k: dists[k])
        if dists[i] <= 45:
            entry = i
            dx, dy = rl[(i + 1) % n][0] - rl[i][0], rl[(i + 1) % n][1] - rl[i][1]
            norm = math.hypot(dx, dy) or 1.0
            dot = (-dy / norm) * (px - rl[i][0]) + (dx / norm) * (py - rl[i][1])
            if abs(dot) > 2:
                side = 1 if dot > 0 else -1

    geometry = {"entry": entry, "length": length, "side": side}
    _pit_geometry_cache[name] = geometry
    return geometry


def pit_lane_position(track, geometry, pos, extra=0.0):
    """Souřadnice na mapě (zdrojové) pro virtuální pozici pos (index + progress) v boxové uličce."""
    rl = track["racing_line"]
    n = len(rl)
    pos %= n
    i = int(pos)
    frac = pos - i
    x1, y1 = rl[i]
    x2, y2 = rl[(i + 1) % n]
    x = x1 + (x2 - x1) * frac
    y = y1 + (y2 - y1) * frac

    d = (pos - geometry["entry"]) % n
    length = geometry["length"]
    if d > length:
        return x, y
    weight = max(0.0, min(1.0, d / PIT_LANE_BLEND, (length - d) / PIT_LANE_BLEND))
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1.0
    offset = (PIT_LANE_OFFSET_PX + extra) * weight * geometry["side"]
    return x + (-dy / norm) * offset, y + (dx / norm) * offset


def pit_box_distance(geometry, team_index, team_count, slot):
    """Kde v uličce (od vjezdu, v bodech trati) stojí box týmu; druhý jezdec o kousek dřív."""
    fraction = 0.3 + 0.4 * team_index / max(1, team_count - 1)
    return geometry["length"] * fraction - 0.12 * slot

# === STARTOVNÍ SEMAFOR (po formačním kole) ===
# Jako ve skutečné F1: 5 červených světel se rozsvěcí po jednom v 1s intervalech,
# pak náhodná prodleva a všechna světla naráz zhasnou = start závodu. Časuje se v
# REÁLNÝCH sekundách (nezávisle na time_scale/time_compression), aby sekvence vypadala
# vždy stejně; při pauze stojí.
START_LIGHTS_COUNT = 5
START_LIGHT_INTERVAL = 1.0      # s mezi rozsvícením dvou světel
START_HOLD_MIN = 0.2            # s po rozsvícení všech 5 světel než zhasnou (náhodně v rozsahu)
START_HOLD_MAX = 3.0
START_LIGHTS_OUT_DISPLAY = 1.5  # s, po které zůstane na obrazovce nápis "světla zhasla"
# Hned po startu stojí auta těsně za sebou (rozestupy jsou hluboko pod prahem souboje v
# handle_battles), takže by se pole hned první snímek náhodně "přeskákalo". Po zhasnutí
# světel se proto souboje o pozice na chvíli (race_time sekundy) vypnou - pole se nejdřív
# přirozeně roztáhne, jako v první zatáčce.
START_NO_BATTLE_SECONDS = 8.0

SAFETY_CAR_DURATION = 8.0
VSC_DURATION = 6.0
RED_FLAG_DURATION = 5.0

DRS_GAP_THRESHOLD = 3.5  # max. odstup (ve stejných jednotkách jako track_index) pro aktivaci DRS
DRS_FIRST_LAP = 3        # DRS se povoluje až od 3. kola (jako ve F1 - první dvě kola je zakázané)

# === SAFETY CAR – seřazování do vláčku ===
SAFETY_CAR_PACE = 0.34             # základní rychlost SC a aut, která už jsou ve frontě (body/s)
SAFETY_CAR_LEADER_GAP = 2.5        # cílový odstup lídra od SC (ve stejných jednotkách jako track_index)
SAFETY_CAR_CAR_GAP = 1.6           # cílový odstup mezi jednotlivými auty ve frontě
SAFETY_CAR_MAX_CATCHUP_TIME = 25.0  # i auto ztracené o celé kolo dožene frontu nejpozději za tolik sekund
SAFETY_CAR_LINEUP_TOLERANCE = 2.0  # největší dovolená mezera od cílové pozice, aby se pole považovalo za seřazené

#Ai si vybíra kola
def ai_choose_tire(driver, race):
    """AI si vybírá gumy podle vlhkosti trati (s osobním weather_bias)."""
    wetness = race.track_wetness + driver.weather_bias
    if wetness >= AI_WET_TIRE_WETNESS:
        return "WET"
    if wetness >= AI_INTER_WETNESS:
        return "INTER"
    if random.random() < 0.92:
        return "HARD" if driver.current_lap > 25 else "MEDIUM" if driver.current_lap > 10 else "SOFT"
    return "MEDIUM"                 # výjimečná chyba

class Screen:
    def handle_events(self, events):
        pass
    
    def update(self, delta_time):
        pass
    
    def draw(self, screen):
        pass
    
class MenuScreen(Screen):
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 28)
        self.font_big = pygame.font.SysFont("arial", 48)

        self.buttons = [
            {"key": "CHAMPIONSHIP", "rect": pygame.Rect(800, 340, 320, 65), "action": GAME_STATE_RACE},
            {"key": "PRACTICE",     "rect": pygame.Rect(800, 420, 320, 65), "action": GAME_STATE_PRACTICE},
            {"key": "SETTINGS",     "rect": pygame.Rect(800, 500, 320, 65), "action": GAME_STATE_SETTINGS},
            {"key": "VYPNOUT",      "rect": pygame.Rect(800, 580, 320, 65), "action": "QUIT"}
        ]

    def handle_events(self, events):
        global current_screen
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = get_mouse_pos()
                for btn in self.buttons:
                    if btn["rect"].collidepoint(mouse_pos):
                        if btn["action"] == "QUIT":
                            pygame.quit()
                            sys.exit()
                        else:
                            change_screen(btn["action"])

    def draw(self, screen):
        screen.fill((7, 7, 17))

        # Gradient
        for i in range(HEIGHT):
            intensity = int(28 * (1 - i / HEIGHT))
            color = (intensity + 8, max(0, intensity - 18), intensity + 12)
            pygame.draw.line(screen, color, (0, i), (WIDTH, i))

        pygame.draw.rect(screen, (35, 0, 25), (0, 0, WIDTH, 280))

        title = self.font_big.render(get_text("F1 MANAGER"), True, (255, 215, 0))
        screen.blit(title, title.get_rect(centerx=960, centery=205))

        subtitle = self.font.render(get_text("2025 SEASON"), True, (180, 180, 210))
        screen.blit(subtitle, subtitle.get_rect(centerx=960, centery=265))

        mouse_pos = get_mouse_pos()
        
        for btn in self.buttons:
            hovered = btn["rect"].collidepoint(mouse_pos)
            
            if hovered:
                pygame.draw.rect(screen, (45, 45, 70), btn["rect"])
                border_color = (255, 215, 0)
                text_color = (255, 215, 0)
            else:
                pygame.draw.rect(screen, (22, 22, 38), btn["rect"])
                border_color = (200, 200, 210)
                text_color = (240, 240, 255)

            pygame.draw.rect(screen, border_color, btn["rect"], 5)

            text = self.font.render(get_text(btn["key"]), True, text_color)
            screen.blit(text, text.get_rect(center=btn["rect"].center))

def ai_choose_pace(driver, race_progress, wetness):
    
    # zničené gumy
    if driver.tire_wear > 0.8:
        return "SAVE"
    
    # mokrá trať
    if wetness > 0.5:
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
    if race.track_wetness > 0.3:
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

    if driver.in_pit or driver.on_pit_lane or driver.pit_requested:
        return False

    # Změna podmínek na trati (déšť / schnutí) se řeší hned, bez ohledu na poslední pit
    wetness = race.track_wetness + driver.weather_bias
    wrong_tire = False
    if driver.tire in DRY_TIRES:
        wrong_tire = wetness >= AI_INTER_WETNESS
    elif driver.tire == "INTER":
        wrong_tire = wetness >= AI_WET_TIRE_WETNESS or (wetness <= AI_INTER_TO_DRY and race.current_weather != "RAIN")
    elif driver.tire == "WET":
        wrong_tire = wetness <= AI_WET_TO_INTER
    if wrong_tire:
        driver.next_tire = ai_choose_tire(driver, race)
        return True

    if driver.current_lap - driver.last_pit_lap < 6:
        return False

    # Základní podmínky
    if driver.tire_wear > 0.88:
        driver.next_tire = ai_choose_tire(driver, race)
        return True

    # === UNDERCUT / OVERCUT LOGIKA ===
    # (driver.current_stint_laps se počítá centrálně při dojetí kola v update(),
    # ne tady - jinak by rostlo podle počtu AI rozhodovacích tiků, ne podle kol)

    # Najdeme nejlepšího soupeře před ním
    # (stejný poziční vzorec jako handle_battles/Safety Car - dřív se tu místo
    # skutečné délky racing_line používala natvrdo *100, což by se rozbilo na
    # každé trati s víc než 100 body racing line)
    path_len = len(race.current_track["racing_line"])
    ahead = None
    min_gap = 999
    for d in race.drivers:
        if d == driver: continue
        gap = (d.current_lap * path_len + d.track_index + d.progress) - \
              (driver.current_lap * path_len + driver.track_index + driver.progress)
        if 0 < gap < min_gap:
            min_gap = gap
            ahead = d

    # UNDERCUT (pitnu dříve než soupeř)
    if ahead and ahead.current_stint_laps > 4 and driver.current_stint_laps >= 7:
        if min_gap < 8 and random.random() < (0.65 * driver.strategy_aggression):
            print(f"🔥 UNDERCUT! {driver.name} pituje před {ahead.name}")
            driver.next_tire = ai_choose_tire(driver, race)
            return True

    # OVERCUT (zůstanu déle)
    # target_stint_end je ABSOLUTNÍ číslo kola (current_lap + délka stintu při
    # naplánování), proto se porovnává s driver.current_lap, ne s current_stint_laps.
    if driver.current_lap >= driver.target_stint_end - 3:
        if random.random() < 0.4:                     # 40% šance na overcut
            print(f"⏳ OVERCUT {driver.name} – prodlužuji stint")
            driver.target_stint_end += 2
            return False

    # Normální pit podle plánu
    if driver.current_lap >= driver.target_stint_end:
        driver.next_tire = ai_choose_tire(driver, race)
        return True

    return False

def generate_incident(driver, race):
    """Snížená šance na incidenty + odstraněno DNF kvůli palivu"""
    if driver.is_dnf or driver.incident_cooldown > 0:
        driver.incident_cooldown = max(0, driver.incident_cooldown - 1)
        return False

    roll = random.random()

    # Mokrá trať a špatné gumy (slick v dešti) zvyšují riziko nehody
    risk = 1.0 + 1.5 * race.track_wetness
    if tire_grip(driver.tire, race.track_wetness) < 0.8:
        risk += 2.5

    # Velmi nízká šance na jakýkoliv incident
    if roll < 0.004 * risk:          # ~1x za 40–50 sekund při 20x
        # Lehká nehoda → Yellow flag
        driver.engine_damage += 0.35
        race.yellow_flag_active = True
        print(f"🟡 ŽLUTÁ VLÁJKA – {driver.name} měl spin!")
        driver.incident_cooldown = 10
        return True

    elif roll < 0.007 * risk:        # Motor / Crash
        driver.is_dnf = True
        driver.dnf_reason = random.choice(["Engine", "Crash", "Big Shunt", "Spin + Wall"])
        driver.finished = True
        print(f"💥 DNF – {driver.name} ({driver.dnf_reason})")

        if random.random() < 0.55:
            if race.safety_car_active:
                # SC už jede - jen prodloužíme jeho trvání, ale neresetujeme
                # rozjeté seřazování pole (jinak by se fronta nikdy nedala dohromady)
                race.safety_car_timer = max(race.safety_car_timer, random.uniform(8, 15))
            else:
                race.deploy_safety_car(12, 28)
        else:
            race.vsc_active = True
            race.vsc_timer = random.uniform(8, 18)
        return True

    return False

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
        self.track_wetness = 0.0          # vlhkost trati 0 (sucho) - 1 (úplně mokro)
        self._weather_overlay = None      # cache průhledné vrstvy přes mapu (mokro/oblačno)
        self.weather_last_check_lap = -1  # poslední kolo (lídra), kdy se losovalo počasí
        self.vsc_active = False
        self.vsc_timer = 0.0
        self.yellow_flag_active = False
        self.yellow_flag_timer = 0.0

        # === SAFETY CAR ===
        self.safety_car_active = False
        self.safety_car_timer = 0.0
        self.safety_car_index = 0
        self.safety_car_progress = 0.0
        self.safety_car_laps = 0          # kumulativní počet průjezdů SC (pro porovnání pozic s jezdci)
        self.safety_car_lined_up = False  # True, jakmile je celé pole seřazené ve vláčku za SC
        self.safety_car_phase = "NONE"    # "DEPLOYED", "LEADING", "ENDING"

        self.selected_driver = None
        self.time_scale = 1
        self.paused = False
        self.race_finished = False

        self.driver_rects = []
        self.speed_buttons = []
        self.pause_button = None
        self.pit_button1 = None
        self.next_race_button = None
        self.pit_button2 = None
        self.start_season_button = None

        self.show_tire_select = False
        self.tire_select_for = None
        self.tire_select_buttons = []

        # === UKLÁDÁNÍ HRY ===
        self.save_message = ""
        self.save_message_timer = 0.0
        self.save_folder = os.path.join(SCRIPT_DIR, "saves")
        os.makedirs(self.save_folder, exist_ok=True)   # vytvoří složku saves, pokud neexistuje

        self._initialize_championship()

        self.save_list = []
        self.selected_save_index = 0

        self.show_ingame_menu = False

        self.race_phase = RACE_PHASE_FORMATION
        self.formation_lap_completed = False
        self.start_audio_played = False
        self.start_lights_on = 0                 # kolik světel semaforu právě svítí (0-5)
        self.start_timer = 0.0                   # reálné sekundy od začátku semaforu
        self.start_hold_time = random.uniform(START_HOLD_MIN, START_HOLD_MAX)
        self.start_lights_out_timer = 0.0        # jak dlouho ještě ukazovat "světla zhasla"
        self.race_start_time = 0.0               # race_time, kdy zhasla světla

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

        # === NASTAVENÍ DÉLKY A RYCHLOSTI ZÁVODU ===
        original_laps = self.current_track.get("laps", 58)
        self.current_track["laps"] = original_laps   # oba módy mají plný počet kol

        if CURRENT_RACE_MODE == "FULL":
            self.time_compression = 1.0          # reálný čas
            print(f"🏎️ FULL RACE - {original_laps} kol | Reálný čas na kolo")
        else:  # SHORT
            self.time_compression = 0.35         # výrazně zrychleno (uprav podle chuti)
            print(f"🏎️ SHORT RACE - {original_laps} kol | Zrychlený čas ({self.time_compression}x)")

        # Načtení mapy
        try:
            map_path = os.path.join(SCRIPT_DIR, self.current_track["map"])
            self.track_image = pygame.image.load(map_path)
            self.track_image = pygame.transform.scale(self.track_image,
                (self.track_display_width, self.track_display_height))
        except Exception as e:
            print(f"Chyba načtení mapy: {e}")
            self.track_image = None

        # Reset jezdců
        for driver in self.drivers:
            driver.track_index = 0
            driver.progress = 0.0
            driver.current_lap = 0
            driver.finished = False
            driver.race_points = 0
            driver.pit_requested = False
            driver.in_pit = False
            driver.on_pit_lane = False
            driver.pit_phase = None
            driver.pit_timer = 0.0
            driver.tire_wear = 0.0
            driver.last_pit_lap = -10
            driver.tire = "MEDIUM"
            driver.next_tire = "MEDIUM"
            driver.total_time = 0.0
            driver.drs_active = False
            driver.strategy_aggression = random.uniform(0.75, 1.35)
            driver.weather_bias = random.uniform(-0.06, 0.08)
            driver.planned_stops = 2 if random.random() < 0.7 else 1
            driver.is_dnf = False
            driver.dnf_reason = None
            driver.incident_cooldown = 0

            ai_plan_stint(driver, self, True)

        # Startovní rošt - pořadí odpovídá aktuálnímu pořadí v self.drivers
        # (stejné, v jakém se zobrazuje na startu leaderboardu).
        for grid_i, driver in enumerate(self.drivers):
            driver.grid_position = grid_i
            driver.formation_start_delay = grid_i * FORMATION_GRID_GAP

        self.race_time = 0.0
        self.race_finished = False
        self.current_weather = "SUN"
        self.track_wetness = 0.0
        self.weather_last_check_lap = -1
        self.safety_car_active = False
        self.safety_car_timer = 0.0
        self.safety_car_index = 0
        self.safety_car_progress = 0.0
        self.safety_car_laps = 0
        self.safety_car_lined_up = False
        self.vsc_active = False
        self.yellow_flag_active = False

        self.race_phase = RACE_PHASE_FORMATION
        self.formation_lap_completed = False
        self.start_audio_played = False
        self.start_lights_on = 0                 # kolik světel semaforu právě svítí (0-5)
        self.start_timer = 0.0                   # reálné sekundy od začátku semaforu
        self.start_hold_time = random.uniform(START_HOLD_MIN, START_HOLD_MAX)
        self.start_lights_out_timer = 0.0        # jak dlouho ještě ukazovat "světla zhasla"
        self.race_start_time = 0.0               # race_time, kdy zhasla světla

        print(f"✅ {CURRENT_RACE_MODE} režim spuštěn - {original_laps} kol")

    def finish_race(self):
        if self.race_finished:
            return
        self.race_finished = True
        
        # Seřazení dokončených jezdců (bez DNF)
        finished_drivers = [d for d in self.drivers if d.finished and not d.is_dnf]
        finished_drivers.sort(key=lambda d: d.total_time if d.total_time > 0 else 999999)
        
        for driver in self.drivers:
            driver.race_points = 0
        for i, driver in enumerate(finished_drivers):
            if i < len(POINTS):
                pts = POINTS[i]
                driver.race_points = pts
                driver.points += pts

        for team in self.teams.values():
            team.update_points()

        # === AUTOMATICKÉ ULOŽENÍ PO ZÁVODĚ ===
        self.save_game(slot=1)   # uloží do slotu 1
        print("💾 Automatické uložení po závodě provedeno.")

    def leave_results(self):
        """Tlačítko "Další závod" na výsledkovém okně (po posledním závodě návrat do menu)."""
        if self.current_race_index + 1 >= len(CALENDAR_2025):
            change_screen(GAME_STATE_MENU)
        else:
            self.next_race()

    def next_race(self):
        self.current_race_index += 1
        if self.current_race_index >= len(CALENDAR_2025):
            print("Sezóna skončila!")
            return False
        self._load_race()
        return True
    
    def save_game(self, slot=1):
        """Uloží hru do vybraného slotu"""
        if self.state != "RACE" or not hasattr(self, 'player_team') or not self.player_team:
            self.save_message = "Ukládání možné jen během závodu!"
            self.save_message_timer = 3.0
            print("❌ " + self.save_message)
            return

        # Vytvoření názvu souboru
        track_name = self.current_track["name"] if self.current_track else "Unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"save{slot}_{track_name.replace(' ', '_')}_Round{self.championship_round}_{timestamp}.json"
        filepath = os.path.join(self.save_folder, filename)

        save_data = {
            "save_version": "1.1",
            "timestamp": datetime.now().isoformat(),
            "current_race_index": self.current_race_index,
            "championship_round": self.championship_round,
            "race_time": round(self.race_time, 2),
            "current_weather": self.current_weather,
            "track_wetness": round(self.track_wetness, 3),
            "safety_car_active": self.safety_car_active,
            "safety_car_timer": round(self.safety_car_timer, 2),
            "vsc_active": self.vsc_active,
            "vsc_timer": round(self.vsc_timer, 2),
            "yellow_flag_active": self.yellow_flag_active,
            "time_scale": self.time_scale,
            "paused": self.paused,
            "race_finished": self.race_finished,
            "player_team_name": self.player_team.name,
            "teams": {},
            "drivers": []
        }

        # Týmy
        for team_name, team in self.teams.items():
            save_data["teams"][team_name] = {"points": team.points}

        # Jezdci
        for driver in self.drivers:
            driver_data = {
                "name": driver.name,
                "team_name": driver.team_name,
                "points": driver.points,
                "base_lap_time": round(driver.base_lap_time, 4),
                "tire": driver.tire,
                "next_tire": driver.next_tire,
                "tire_wear": round(driver.tire_wear, 4),
                "current_lap": driver.current_lap,
                "total_time": round(driver.total_time, 2),
                "track_index": driver.track_index,
                "progress": round(driver.progress, 4),
                "pace_mode": driver.pace_mode,
                "strategy_aggression": round(driver.strategy_aggression, 4),
                "planned_stops": driver.planned_stops,
                "current_stint_laps": driver.current_stint_laps,
                "target_stint_end": driver.target_stint_end,
                "last_pit_lap": driver.last_pit_lap,
                "is_dnf": driver.is_dnf,
                "dnf_reason": driver.dnf_reason,
                "drs_active": driver.drs_active,
                "in_pit": driver.in_pit,
                "pit_timer": round(driver.pit_timer, 2)
            }
            save_data["drivers"].append(driver_data)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            
            self.save_message = f"Hra uložena! (Slot {slot})"
            self.save_message_timer = 3.0
            print(f"✅ Hra uložena jako: {filename}")
        except Exception as e:
            self.save_message = "Chyba při ukládání!"
            self.save_message_timer = 3.0
            print(f"❌ Chyba ukládání: {e}")

    def load_game(self, slot=1):
        """Načte hru z vybraného slotu (načte nejnovější soubor v daném slotu)"""
        if not os.path.exists(self.save_folder):
            self.save_message = "Žádné uložené hry!"
            self.save_message_timer = 3.0
            return False

        # Najdeme všechny soubory pro daný slot
        files = [f for f in os.listdir(self.save_folder) if f.startswith(f"save{slot}_") and f.endswith(".json")]
        if not files:
            self.save_message = f"Slot {slot} je prázdný!"
            self.save_message_timer = 3.0
            return False

        # Seřadíme podle data vytvoření (nejnovější první)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.save_folder, x)), reverse=True)
        filepath = os.path.join(self.save_folder, files[0])

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            # Obnovení základních hodnot
            self.current_race_index = save_data["current_race_index"]
            self.championship_round = save_data["championship_round"]
            self.race_time = save_data["race_time"]
            self.current_weather = save_data["current_weather"]
            self.track_wetness = save_data.get("track_wetness", 0.0)
            self.safety_car_active = save_data["safety_car_active"]
            self.safety_car_timer = save_data["safety_car_timer"]
            self.safety_car_index = 0
            self.safety_car_progress = 0.0
            self.safety_car_laps = 0
            self.safety_car_lined_up = False
            self.vsc_active = save_data["vsc_active"]
            self.vsc_timer = save_data["vsc_timer"]
            self.yellow_flag_active = save_data["yellow_flag_active"]
            self.time_scale = save_data.get("time_scale", 1)
            self.paused = save_data.get("paused", False)
            self.race_finished = save_data.get("race_finished", False)

            # Obnovení týmů
            for team_name, data in save_data["teams"].items():
                if team_name in self.teams:
                    self.teams[team_name].points = data["points"]

            # Obnovení jezdců
            for d_data in save_data["drivers"]:
                for driver in self.drivers:
                    if driver.name == d_data["name"]:
                        driver.points = d_data["points"]
                        driver.tire = d_data["tire"]
                        driver.next_tire = d_data["next_tire"]
                        driver.tire_wear = d_data["tire_wear"]
                        driver.current_lap = d_data["current_lap"]
                        driver.total_time = d_data["total_time"]
                        driver.track_index = d_data["track_index"]
                        driver.progress = d_data["progress"]
                        driver.pace_mode = d_data["pace_mode"]
                        driver.strategy_aggression = d_data["strategy_aggression"]
                        driver.planned_stops = d_data["planned_stops"]
                        driver.current_stint_laps = d_data["current_stint_laps"]
                        driver.target_stint_end = d_data["target_stint_end"]
                        driver.last_pit_lap = d_data["last_pit_lap"]
                        driver.is_dnf = d_data["is_dnf"]
                        driver.dnf_reason = d_data.get("dnf_reason")
                        driver.drs_active = d_data.get("drs_active", False)
                        driver.in_pit = d_data.get("in_pit", False)
                        driver.pit_timer = d_data.get("pit_timer", 0.0)
                        break

            self._load_race()

            self.save_message = f"Načteno: {files[0]}"
            self.save_message_timer = 4.0
            print(f"✅ Hra načtena: {files[0]}")
            return True

        except Exception as e:
            self.save_message = "Chyba při načítání!"
            self.save_message_timer = 3.0
            print(f"❌ Chyba načítání: {e}")
            return False
        
    def list_saves(self):
        """Vrátí seznam všech uložených her"""
        if not os.path.exists(self.save_folder):
            return []
        
        saves = []
        for file in os.listdir(self.save_folder):
            if file.endswith(".json"):
                try:
                    path = os.path.join(self.save_folder, file)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    saves.append({
                        "filename": file,
                        "date": data.get("timestamp", "Neznámé"),
                        "track": data.get("current_track_name", "Neznámá"),
                        "round": data.get("championship_round", "?"),
                        "race_time": round(data.get("race_time", 0), 1)
                    })
                except:
                    continue
        return saves
    
    def show_save_list(self):
        """Zobrazí grafický seznam uložených her"""
        self.save_list = self.list_saves()
        self.selected_save_index = 0
        self.state = "SAVE_LIST"
        self.show_ingame_menu = False   # zavře in-game menu
        self.paused = True

    def update(self, delta_time):
        if self.paused or not self.current_track or self.race_finished:
            return
        
        if self.save_message_timer > 0:
            self.save_message_timer -= delta_time
        
        real_delta_time = delta_time  # před time_scale - pro startovní semafor
        delta_time *= self.time_scale
        self.race_time += delta_time

        # Počasí - losuje se podle odjetých kol lídra, ne podle uplynulého reálného
        # času. Jedno kolo trvá desítky až stovky race-time sekund (podle tratě a
        # time_compression), takže dřívější časový časovač (18s) přehazoval počasí
        # i 5-10x za jedno kolo (skoro jistý déšť hned na startu).
        leader_lap_for_weather = max(
            (d.current_lap for d in self.drivers if not d.finished and not d.is_dnf),
            default=0,
        )
        if (leader_lap_for_weather != self.weather_last_check_lap
                and leader_lap_for_weather > 0
                and leader_lap_for_weather % WEATHER_CHANGE_LAPS == 0):
            self.weather_last_check_lap = leader_lap_for_weather
            self.current_weather = next_weather(self.current_weather)

        # Vlhkost trati se mění podle "kol" (jedno kolo = path_len / time_compression race-sekund),
        # takže rychlost mokření/schnutí je stejná na všech tratích i v SHORT/FULL.
        lap_race_seconds = len(self.current_track["racing_line"]) / max(0.05, getattr(self, 'time_compression', 1.0))
        if self.current_weather == "RAIN":
            self.track_wetness += delta_time / (WETTING_LAPS * lap_race_seconds)
        else:
            self.track_wetness -= delta_time / (DRYING_LAPS[self.current_weather] * lap_race_seconds)
        self.track_wetness = max(0.0, min(1.0, self.track_wetness))

        # === SAFETY CAR LOGIKA (jako ve skutečné F1) ===
        if (random.random() < 0.001 * (1.0 + 1.5 * self.track_wetness) and not self.safety_car_active
                and self.race_phase == RACE_PHASE_RACING and self.race_time > 25):
            self.deploy_safety_car(20, 55)
            print("🚨 SAFETY CAR OUT - Jezdci se seřazují za ním!")

        path = self.current_track["racing_line"]
        path_len = len(path)

        if self.safety_car_active:
            self.safety_car_timer -= delta_time
            # Pohyb Safety Caru (stejné tempo jako auta v koloně za ním)
            self.safety_car_progress += SAFETY_CAR_PACE * getattr(self, 'time_compression', 1.0) * delta_time
            while self.safety_car_progress >= 1.0:
                self.safety_car_progress -= 1.0
                self.safety_car_index = (self.safety_car_index + 1) % path_len
                if self.safety_car_index == 0:
                    self.safety_car_laps += 1

            self.update_safety_car_queue()

            if self.safety_car_timer <= 0 and self.safety_car_lined_up:
                self.safety_car_active = False
                self.safety_car_lined_up = False
                print("🏁 SAFETY CAR IN - Závod pokračuje!")
        else:
            self._sc_speed_overrides = {}

        if self.vsc_active:
            self.vsc_timer -= delta_time
            if self.vsc_timer <= 0:
                self.vsc_active = False

        if self.yellow_flag_active:
            self.yellow_flag_timer += delta_time
            if self.yellow_flag_timer > 6:
                self.yellow_flag_active = False
                self.yellow_flag_timer = 0

        race_progress = max((d.current_lap for d in self.drivers if not d.finished), default=0) / self.current_track["laps"]

        for driver in self.drivers:
            if driver.finished or driver.is_dnf:
                continue

            driver.ai_decision_timer += delta_time

            if self.race_phase == RACE_PHASE_RACING and random.random() < 0.012 and not driver.is_dnf:
                generate_incident(driver, self)

            # AI rozhodnutí (před startem - formační kolo a semafor - se nepituje ani nemění tempo)
            if (self.race_phase == RACE_PHASE_RACING and
                driver != self.player_team.drivers[0] and
                driver != self.player_team.drivers[1] and
                driver.ai_decision_timer > 0.9):

                driver.pace_mode = ai_choose_pace(driver, race_progress, self.track_wetness)
                
                if ai_should_pit(driver, self):
                    driver.pit_requested = True
                    driver.last_pit_lap = driver.current_lap
                
                
                driver.ai_decision_timer = 0

            # === ZÍSKÁNÍ RYCHLOSTI (včetně SC) ===
            speed = get_speed(driver, self)
            
            # === TIME COMPRESSION (rozdíl mezi SHORT a FULL) ===
            speed *= getattr(self, 'time_compression', 1.0)

            # Základní posun
            segments_per_sec = path_len / max(1.0, driver.base_lap_time * 1.1)
            driver.progress += speed * delta_time

            while driver.progress >= 1.0:
                driver.progress -= 1.0
                driver.track_index = (driver.track_index + 1) % path_len
                
                if driver.track_index == 0:
                    driver.current_lap += 1
                    driver.current_stint_laps += 1
                    driver.total_time = self.race_time
                    
                    if self.race_phase == RACE_PHASE_FORMATION and driver.current_lap >= 1:
                        self.formation_lap_completed = True
                        self.race_phase = RACE_PHASE_START

            # Opotřebení kol - škáluje se podle skutečně ujeté vzdálenosti (ne podle
            # uplynulého času), takže je konzistentní napříč tratěmi (různá délka
            # racing_line) i time_scale/time_compression. `speed * delta_time` je
            # přesně vzdálenost ujetá tento frame (stejná hodnota, co jde do
            # driver.progress o pár řádků výš).
            lap_fraction = (speed * delta_time) / path_len if path_len else 0.0
            driver.tire_wear += (lap_fraction * PACE[driver.pace_mode]["wear"] * TIRE_WEAR_PER_LAP[driver.tire]
                                 * tire_wear_weather_factor(driver.tire, self.track_wetness))
            driver.tire_wear = min(1.0, driver.tire_wear)

            # Pit stop (vjezd do uličky, zastávka u boxu, odjezd)
            self._update_pit(driver, delta_time, path_len)

        # === KONEC ZÁVODU ===
        # Tie-break musí jít přes celou poziční hodnotu, ne jen current_lap - jinak
        # při shodném počtu kol vyhraje "lídra" jen náhodou první jezdec v
        # self.drivers, i když je ve skutečnosti (track_index/progress) vzadu.
        leader = max(self.drivers, key=lambda d: d.current_lap * path_len + d.track_index + d.progress)
        target_laps = self.current_track["laps"]

        if leader.current_lap > target_laps and not self.race_finished:
            print(f"🏁 Závod skončil! Leader dokončil {target_laps} kol.")
            # Všichni zbývající jezdci se dokončí NAJEDNOU v tomto framu, takže
            # total_time nemůže vycházet z reálného momentu dojezdu (ten u nich
            # nenastal) - musí se dopočítat z toho, jak daleko za lídrem skutečně
            # jsou (stejná pozice-jako-vzdálenost, co se používá i jinde v kódu),
            # jinak by pořadí v cíli (a tedy i body) odpovídalo jen náhodnému
            # pořadí v self.drivers, ne odjetému závodu.
            leader_pos = leader.current_lap * path_len + leader.track_index + leader.progress
            for driver in self.drivers:
                if not driver.finished and not driver.is_dnf:
                    driver.finished = True
                    if driver is leader:
                        driver.total_time = self.race_time
                    else:
                        driver_pos = driver.current_lap * path_len + driver.track_index + driver.progress
                        pos_diff = max(0.0, leader_pos - driver_pos)
                        estimated_gap = pos_diff * (88 / path_len)  # ~88s/kolo, stejný odhad jako živý leaderboard
                        driver.total_time = self.race_time + estimated_gap
            self.finish_race()

        # Startovní semafor: 5 světel po jednom, náhodná prodleva, zhasnutí = start
        if self.start_lights_out_timer > 0:
            self.start_lights_out_timer = max(0.0, self.start_lights_out_timer - real_delta_time)

        if self.race_phase == RACE_PHASE_START:
            self.start_timer += real_delta_time
            self.start_lights_on = min(START_LIGHTS_COUNT, int(self.start_timer / START_LIGHT_INTERVAL))
            lights_out_at = START_LIGHTS_COUNT * START_LIGHT_INTERVAL + self.start_hold_time
            if self.start_timer >= lights_out_at:
                self.start_lights_on = 0
                self.start_lights_out_timer = START_LIGHTS_OUT_DISPLAY
                self.race_start_time = self.race_time
                self.race_phase = RACE_PHASE_RACING
                self._play_start_comment()

        self.update_drs()
        self.handle_battles()

        if all(d.finished or d.is_dnf for d in self.drivers):
            self.finish_race()

    def _update_pit(self, driver, delta_time, path_len):
        geometry = get_pit_geometry(self.current_track)
        d = ((driver.track_index + driver.progress) - geometry["entry"]) % path_len

        if not driver.in_pit:
            # Žádost o pit se splní, až auto dojede k vjezdu do uličky (ne okamžitě)
            if driver.pit_requested and self.race_phase == RACE_PHASE_RACING and d < PIT_ENTRY_WINDOW:
                team_names = list(self.teams)
                team = self.teams.get(driver.team_name)
                slot = team.drivers.index(driver) if team and driver in team.drivers else 0
                driver.pit_box_d = pit_box_distance(
                    geometry, team_names.index(driver.team_name), len(team_names), slot)
                driver.in_pit = True
                driver.on_pit_lane = True
                driver.pit_phase = "ENTRY"
                driver.pit_requested = False
                driver.pit_timer = 0.0
            return

        if driver.pit_phase == "ENTRY":
            if d >= driver.pit_box_d:
                driver.pit_phase = "SERVICE"
                driver.pit_timer = 0.0
        elif driver.pit_phase == "SERVICE":
            driver.pit_timer += delta_time
            if driver.pit_timer >= PIT_TIME / getattr(self, 'time_compression', 1.0):
                driver.tire = driver.next_tire
                driver.tire_wear = 0.0
                driver.current_stint_laps = 0
                driver.last_pit_lap = driver.current_lap
                if driver not in self.player_team.drivers:
                    ai_plan_stint(driver, self, is_first_stint=False)
                driver.pit_phase = "EXIT"
        else:  # EXIT (a pojistka pro nekonzistentní stav)
            if d >= geometry["length"] or driver.pit_phase is None:
                driver.in_pit = False
                driver.on_pit_lane = False
                driver.pit_phase = None
                driver.pit_timer = 0.0

    def _play_start_comment(self):
        if self.start_audio_played:
            return
        self.start_audio_played = True
        try:
            if CURRENT_LANGUAGE == "CS" and os.path.exists(START_COMMENT_CS):
                pygame.mixer.music.load(START_COMMENT_CS)
                print("▶️ Přehrávám český start komentář")
            elif os.path.exists(START_COMMENT_EN):
                pygame.mixer.music.load(START_COMMENT_EN)
                print("▶️ Playing English start comment")
            else:
                print("⚠️ Audio soubory nenalezeny v 'sounds/' složce")
            pygame.mixer.music.play()
        except Exception as e:
            print(f"❌ Chyba při přehrávání audia: {e}")

    def deploy_safety_car(self, min_duration, max_duration):
        """Nasadí Safety Car na pozici aktuálního lídra, aby na něj mohlo pole postupně navázat."""
        path_len = len(self.current_track["racing_line"]) if self.current_track else 1
        active = [d for d in self.drivers if not d.finished and not d.is_dnf]
        leader = max(
            active,
            key=lambda d: d.current_lap * path_len + d.track_index + d.progress,
            default=None,
        )

        self.safety_car_active = True
        self.safety_car_timer = random.uniform(min_duration, max_duration)
        self.safety_car_lined_up = False

        if leader:
            self.safety_car_laps = leader.current_lap
            self.safety_car_index = leader.track_index
            self.safety_car_progress = leader.progress
        else:
            self.safety_car_laps = 0
            self.safety_car_index = 0
            self.safety_car_progress = 0.0

        self._sc_speed_overrides = {}

    def update_safety_car_queue(self):
        """Spočítá cílové pozice a rychlosti aut, aby se seřadily do vláčku za Safety Carem."""
        path_len = len(self.current_track["racing_line"])
        sc_pos = self.safety_car_laps * path_len + self.safety_car_index + self.safety_car_progress

        queue = [d for d in self.drivers if not d.finished and not d.is_dnf and not d.in_pit]
        queue.sort(key=lambda d: d.current_lap * path_len + d.track_index + d.progress, reverse=True)

        overrides = {}
        worst_gap = 0.0

        for i, driver in enumerate(queue):
            target_pos = sc_pos - SAFETY_CAR_LEADER_GAP - i * SAFETY_CAR_CAR_GAP
            current_pos = driver.current_lap * path_len + driver.track_index + driver.progress
            gap = target_pos - current_pos

            if gap > 0:
                # Rychlost dohánění je úměrná velikosti mezery, takže i auto ztracené
                # o celé kolo dožene frontu nejpozději za SAFETY_CAR_MAX_CATCHUP_TIME sekund.
                overrides[id(driver)] = SAFETY_CAR_PACE + gap / SAFETY_CAR_MAX_CATCHUP_TIME
            else:
                overrides[id(driver)] = 0.0

            worst_gap = max(worst_gap, gap)

        self._sc_speed_overrides = overrides
        self.safety_car_lined_up = worst_gap <= SAFETY_CAR_LINEUP_TOLERANCE

    def get_safety_car_speed(self, driver):
        return getattr(self, '_sc_speed_overrides', {}).get(id(driver), SAFETY_CAR_PACE)

    def update_drs(self):
        # driver.distance se nikde needituje (zůstává 0.0 z __init__), takže
        # `front.distance - driver.distance` bylo vždy 0 a DRS bylo prakticky
        # aktivní pro celé pole pořád (0 < 25 je vždy pravda) - nahrazeno stejným
        # pozičním vzorcem jako handle_battles/Safety Car.
        if not self.current_track:
            return
        path_len = len(self.current_track["racing_line"])
        active = [d for d in self.drivers if not d.finished and not d.is_dnf and not d.in_pit]
        ordered = sorted(active, key=lambda d: d.current_lap * path_len + d.track_index + d.progress, reverse=True)

        for d in self.drivers:
            d.drs_active = False

        if self.race_phase != RACE_PHASE_RACING:
            return  # DRS je před startem (formační kolo, semafor) vypnuté
        if not ordered or ordered[0].current_lap < DRS_FIRST_LAP:
            return  # a v prvních dvou kolech závodu (current_lap = kolo, které lídr právě jede)

        for i, driver in enumerate(ordered):
            if i == 0:
                continue
            front = ordered[i - 1]
            front_pos = front.current_lap * path_len + front.track_index + front.progress
            driver_pos = driver.current_lap * path_len + driver.track_index + driver.progress
            gap = front_pos - driver_pos
            if 0 < gap < DRS_GAP_THRESHOLD and self.track_wetness < DRS_MAX_WETNESS and self.race_time > 5:
                driver.drs_active = True

    def handle_battles(self):
        if not self.current_track or self.safety_car_active or self.race_phase != RACE_PHASE_RACING:
            return  # Žádné předjíždění během Safety Caru ani před startem (formační kolo, semafor)
        if self.race_time - self.race_start_time < START_NO_BATTLE_SECONDS:
            return  # těsně po startu se pole nejdřív roztáhne (viz START_NO_BATTLE_SECONDS)

        path_len = len(self.current_track["racing_line"])
        # Vyřadit dojeté/DNF/pitující jezdce - jinak šlo "předjet" i zaparkované
        # auto po nehodě nebo si spočítat souboj s autem v boxové uličce.
        active = [d for d in self.drivers if not d.finished and not d.is_dnf and not d.in_pit]
        ordered = sorted(active, key=lambda d: d.current_lap * path_len + d.track_index + d.progress, reverse=True)

        for i in range(len(ordered) - 1):
            front = ordered[i]
            behind = ordered[i + 1]
            
            front_pos = front.current_lap * path_len + front.track_index + front.progress
            behind_pos = behind.current_lap * path_len + behind.track_index + behind.progress
            gap = front_pos - behind_pos
            
            if 0 < gap < 2.2:
                front_speed = get_speed(front, self)
                behind_speed = get_speed(behind, self)
                
                attack_chance = 0.065 * behind.overtake_skill
                if behind.drs_active:
                    attack_chance *= 2.4
                
                if behind_speed > front_speed * 0.94 and random.random() < attack_chance:
                    behind.track_index = front.track_index
                    behind.progress = min(front.progress + 0.15, 0.96)
                    print(f"⚡ {behind.name} předjel {front.name}")

    def handle_events(self, events):
        global CURRENT_FPS, IS_FULLSCREEN

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = get_mouse_pos()

                if self.show_ingame_menu:
                    if hasattr(self, 'continue_rect') and self.continue_rect.collidepoint(pos):
                        self.show_ingame_menu = False
                        self.paused = False
                        self.state = "RACE"          # ← důležitý reset
                    elif hasattr(self, 'save_rect') and self.save_rect.collidepoint(pos):
                        self.save_game(slot=1)
                    elif hasattr(self, 'load_rect') and self.load_rect.collidepoint(pos):
                        self.show_save_list()
                    elif hasattr(self, 'settings_rect') and self.settings_rect.collidepoint(pos):
                        change_screen(GAME_STATE_SETTINGS)
                    elif hasattr(self, 'mainmenu_rect') and self.mainmenu_rect.collidepoint(pos):
                        change_screen(GAME_STATE_MENU)
                    elif hasattr(self, 'quit_rect') and self.quit_rect.collidepoint(pos):
                        pygame.quit()
                        sys.exit()
                    return

                # Zbytek handle_events (team select, pit buttons, speed buttons atd.)
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
                    if self.race_finished:
                        if self.next_race_button and self.next_race_button.collidepoint(pos):
                            self.leave_results()
                        return

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
                                chosen = self.player_team.drivers[0 if self.tire_select_for == "driver1" else 1]
                                if not chosen.in_pit and not chosen.is_dnf and not chosen.finished:
                                    chosen.next_tire = tire_type
                                    chosen.pit_requested = True
                                self.show_tire_select = False
                                self.tire_select_buttons = []
                                return

                    if self.pause_button and self.pause_button.collidepoint(pos):
                        self.paused = not self.paused   # pouze pause / unpause

                    for btn in self.speed_buttons:
                        if btn["rect"].collidepoint(pos):
                            self.time_scale = btn["speed"]

                elif self.state == "SAVE_LIST":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = "RACE"
                            self.show_ingame_menu = False   # důležité
                            self.paused = False
                        elif event.key == pygame.K_UP and self.save_list:
                            self.selected_save_index = max(0, self.selected_save_index - 1)
                        elif event.key == pygame.K_DOWN and self.save_list:
                            self.selected_save_index = min(len(self.save_list)-1, self.selected_save_index + 1)
                        elif event.key == pygame.K_RETURN and self.save_list:
                            self.load_game(slot=1)
                            self.state = "RACE"
                            self.show_ingame_menu = False
                            self.paused = False

            # ==================== KLÁVESNICOVÉ OVLÁDÁNÍ ====================
            elif event.type == pygame.KEYDOWN:
                if (self.race_finished and self.state == "RACE" and not self.show_ingame_menu
                        and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)):
                    self.leave_results()
                    return

                if event.key == pygame.K_ESCAPE:
                    if self.show_ingame_menu:
                        self.show_ingame_menu = False
                        self.paused = False
                        self.state = "RACE"
                    elif self.state == "SAVE_LIST":
                        self.state = "RACE"
                        self.show_ingame_menu = False
                        self.paused = False
                    elif self.state == "TEAM_SELECT":
                        change_screen(GAME_STATE_MENU)   # ← NOVÉ
                    else:
                        self.show_ingame_menu = True
                        self.paused = True

                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused

                elif event.key == pygame.K_1: self.time_scale = 1
                elif event.key == pygame.K_2: self.time_scale = 2
                elif event.key == pygame.K_3: self.time_scale = 4
                elif event.key == pygame.K_4: self.time_scale = 20
                elif event.key == pygame.K_TAB:
                    self.time_scale = 20 if self.time_scale == 1 else 1

                # Ukládání a načítání
                elif event.key == pygame.K_s:           # S = Save slot 1
                    self.save_game(slot=1)
                elif event.key == pygame.K_l:           # L = Load slot 1
                    self.load_game(slot=1)
                elif event.key == pygame.K_5:           # 5 = Save slot 2
                    self.save_game(slot=2)
                elif event.key == pygame.K_6:           # 6 = Load slot 2
                    self.load_game(slot=2)

                elif event.key == pygame.K_k:           # K = Seznam uložených her
                    self.show_save_list()

    @staticmethod
    def _pit_button_color(driver):
        """Tlačítko BOX: červené = klid, žluté = pit požadován (čeká na vjezd), zelené = v boxové uličce."""
        if driver.in_pit:
            return (0, 160, 90)
        if driver.pit_requested:
            return (225, 165, 0)
        return (200, 60, 60)

    def _results_data(self):
        """Podklady pro výsledkové okno: pořadí v cíli, pořadí jezdců a týmů (se změnou po tomto závodě)."""
        path_len = len(self.current_track["racing_line"])
        finishers = sorted((d for d in self.drivers if d.finished and not d.is_dnf),
                           key=lambda d: d.total_time if d.total_time > 0 else 999999)
        retired = sorted((d for d in self.drivers if d.is_dnf),
                         key=lambda d: d.current_lap * path_len + d.track_index + d.progress, reverse=True)

        def moves(items, points_of, race_points_of):
            """O kolik míst se položka posunula nahoru (+) / dolů (-) tímto závodem.

            Pořadí se při shodě bodů bere "nejhůř" (rank = kolik položek má aspoň tolik
            bodů). Kdo před závodem neměl žádné body, do pořadí ještě nepatřil - změna
            se u něj neukazuje (None), jinak by se po prvním závodě zobrazovaly výmysly."""
            result = {}
            for item in items:
                before = points_of(item) - race_points_of(item)
                if before <= 0:
                    result[id(item)] = None
                    continue
                rank_before = sum(1 for o in items if points_of(o) - race_points_of(o) >= before)
                rank_after = sum(1 for o in items if points_of(o) >= points_of(item))
                result[id(item)] = rank_before - rank_after
            return result

        teams = list(self.teams.values())
        team_race_points = {t.name: sum(d.race_points for d in t.drivers) for t in teams}
        return {
            "finishers": finishers, "retired": retired,
            "drivers": sorted(self.drivers, key=lambda d: -d.points),
            "teams": sorted(teams, key=lambda t: -t.points),
            "driver_move": moves(self.drivers, lambda d: d.points, lambda d: d.race_points),
            "team_move": moves(teams, lambda t: t.points, lambda t: team_race_points[t.name]),
            "team_race_points": team_race_points,
        }

    def _draw_results_panel(self, screen, rect, title, rows, row_height):
        """Jedno okno výsledků: nadpis + řádky (pos, jméno, barva týmu, sloupce zprava)."""
        pygame.draw.rect(screen, (20, 20, 34), rect, border_radius=10)
        pygame.draw.rect(screen, (255, 215, 0), rect, 3, border_radius=10)
        screen.blit(self.font_big.render(title, True, (255, 215, 0)), (rect.x + 22, rect.y + 14))
        pygame.draw.line(screen, (90, 90, 110), (rect.x + 16, rect.y + 62), (rect.right - 16, rect.y + 62), 2)

        y = rect.y + 72
        for row in rows:
            if row.get("highlight"):
                pygame.draw.rect(screen, (40, 52, 84), (rect.x + 10, y - 3, rect.w - 20, row_height - 4), border_radius=6)
            pygame.draw.rect(screen, row["color"], (rect.x + 64, y + 2, 6, row_height - 12))
            text_y = y + (row_height - 4 - self.font.get_height()) // 2 - 1
            pos_font = self.font_small if len(row["pos"]) > 3 else self.font   # "DNF" se jinak tlačí na barevný proužek týmu
            screen.blit(pos_font.render(row["pos"], True, (200, 200, 215)),
                        (rect.x + 20, y + (row_height - 4 - pos_font.get_height()) // 2 - 1))
            screen.blit(self.font.render(row["name"], True, row["color"]), (rect.x + 82, text_y))
            for text, color, right_offset in row["columns"]:
                surf = self.font.render(text, True, color)
                screen.blit(surf, (rect.right - right_offset - surf.get_width(), text_y))
            y += row_height

    @staticmethod
    def _move_column(move):
        """Změna pozice v pořadí po závodě: zelené +N (posun nahoru), červené -N, šedé =."""
        if move is None:
            return None
        if move > 0:
            return (f"+{move}", (90, 230, 120), 18)
        if move < 0:
            return (f"{move}", (240, 90, 90), 18)
        return ("=", (150, 150, 165), 18)

    def _draw_results_screen(self, screen):
        """Okno po skončení závodu: Race finish / Driver standings / Team standings + tlačítko Další závod."""
        screen.fill((12, 12, 22))
        data = self._results_data()
        track_name = self.current_track["name"].upper()
        last_race = self.current_race_index + 1 >= len(CALENDAR_2025)

        screen.blit(self.font_big.render(f"{get_text('RACE FINISHED')} - {track_name}", True, (255, 215, 0)), (40, 28))
        subtitle = f"{get_text('ROUND')} {self.current_race_index + 1}/{len(CALENDAR_2025)}"
        if last_race:
            subtitle += f"  -  {get_text('SEASON OVER')}"
        screen.blit(self.font.render(subtitle, True, (170, 170, 190)), (40, 70))

        # Tlačítko vpravo nahoře
        self.next_race_button = pygame.Rect(WIDTH - 40 - 400, 22, 400, 68)
        hovered = self.next_race_button.collidepoint(get_mouse_pos())
        pygame.draw.rect(screen, (110, 225, 130) if hovered else (80, 200, 100), self.next_race_button, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.next_race_button, 3, border_radius=10)
        label = get_text("NÁVRAT DO MENU") if last_race else get_text("NEXT RACE")
        label_surf = self.font_big.render(label, True, (255, 255, 255))
        screen.blit(label_surf, label_surf.get_rect(center=self.next_race_button.center))

        # Tři okna vedle sebe
        gap = 30
        panel_w = (WIDTH - 2 * 40 - 2 * gap) // 3
        panel_y, panel_h = 118, HEIGHT - 118 - 30
        panels = [pygame.Rect(40 + i * (panel_w + gap), panel_y, panel_w, panel_h) for i in range(3)]
        team_color = lambda name: self.teams[name].color
        mine = self.player_team.name if self.player_team else None
        pts = get_text("PTS")

        # 1) výsledky závodu
        rows = []
        winner_time = data["finishers"][0].total_time if data["finishers"] else 0.0
        for i, driver in enumerate(data["finishers"]):
            if i == 0:
                gap_text = format_race_time(driver.total_time)
            else:
                gap_s = driver.total_time - winner_time
                if gap_s >= 88:   # stejný odhad "88 s na kolo" jako živý leaderboard
                    laps_down = int(gap_s // 88)
                    gap_text = f"+{laps_down} {get_text('LAP' if laps_down == 1 else 'LAPS')}"
                else:
                    gap_text = f"+{gap_s:.1f}s"
            columns = [(gap_text, (215, 215, 225), 96 if driver.race_points else 18)]
            if driver.race_points:
                columns.append((f"+{driver.race_points}", (255, 215, 0), 18))
            rows.append({"pos": f"{i + 1}.", "name": driver.name, "color": team_color(driver.team_name),
                         "columns": columns, "highlight": driver.team_name == mine})
        for driver in data["retired"]:
            reason = get_text(driver.dnf_reason) if driver.dnf_reason else ""
            rows.append({"pos": "DNF", "name": driver.name, "color": (200, 90, 90),
                         "columns": [(reason, (200, 90, 90), 18)], "highlight": driver.team_name == mine})
        self._draw_results_panel(screen, panels[0], get_text("RACE FINISH"), rows, 40)

        # 2) pořadí jezdců
        rows = []
        for i, driver in enumerate(data["drivers"]):
            columns = [(f"{driver.points} {pts}", (235, 235, 245), 150)]
            if driver.race_points:
                columns.append((f"+{driver.race_points}", (255, 215, 0), 92))
            move_column = self._move_column(data["driver_move"][id(driver)])
            if move_column:
                columns.append(move_column)
            rows.append({"pos": f"{i + 1}.", "name": driver.name, "color": team_color(driver.team_name),
                         "columns": columns, "highlight": driver.team_name == mine})
        self._draw_results_panel(screen, panels[1], get_text("DRIVER STANDINGS"), rows, 40)

        # 3) pořadí týmů
        rows = []
        for i, team in enumerate(data["teams"]):
            race_pts = data["team_race_points"][team.name]
            columns = [(f"{team.points} {pts}", (235, 235, 245), 150)]
            if race_pts:
                columns.append((f"+{race_pts}", (255, 215, 0), 92))
            move_column = self._move_column(data["team_move"][id(team)])
            if move_column:
                columns.append(move_column)
            rows.append({"pos": f"{i + 1}.", "name": team.name, "color": team.color,
                         "columns": columns, "highlight": team.name == mine})
        self._draw_results_panel(screen, panels[2], get_text("TEAM STANDINGS"), rows, 62)

    def _draw_start_lights(self, screen):
        """Pětice startovních světel jako na F1 semaforu (2 světla nad sebou v každém sloupci)."""
        radius = 18
        pitch = 54
        pad = 14
        panel_w = (START_LIGHTS_COUNT - 1) * pitch + 2 * radius + 2 * pad
        panel_h = 2 * (2 * radius) + 8 + 2 * pad
        map_center_x = 480 + 720 // 2
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.midtop = (map_center_x, 438)  # pod tratí, aby nezakrývala okruh

        pygame.draw.rect(screen, (14, 14, 18), panel, border_radius=12)
        pygame.draw.rect(screen, (90, 90, 100), panel, 3, border_radius=12)

        for i in range(START_LIGHTS_COUNT):
            cx = panel.left + pad + radius + i * pitch
            lit = i < self.start_lights_on
            for row in range(2):
                cy = panel.top + pad + radius + row * (2 * radius + 8)
                pygame.draw.circle(screen, (5, 5, 5), (cx, cy), radius + 3)
                if lit:
                    pygame.draw.circle(screen, (235, 20, 20), (cx, cy), radius)
                    pygame.draw.circle(screen, (255, 120, 120), (cx - 5, cy - 5), 5)
                else:
                    pygame.draw.circle(screen, (48, 14, 14), (cx, cy), radius)

    def draw(self, screen):
        # F1 carbon dark background
        screen.fill((12, 12, 22))

                # === IN-GAME MENU (ESC) ===
        if self.show_ingame_menu:
            # Tmavý overlay
            overlay = pygame.Rect(460, 200, 1000, 620)
            s = pygame.Surface((1000, 620))
            s.set_alpha(235)
            s.fill((8, 8, 25))
            screen.blit(s, (460, 200))
            pygame.draw.rect(screen, (255, 215, 0), overlay, 6)

            title = self.font_big.render(get_text("PAUSED"), True, (255, 215, 0))
            screen.blit(title, title.get_rect(centerx=960, centery=255))

            # Vycentrovaná tlačítka
            self.continue_rect = pygame.Rect(720, 320, 480, 65)
            self.save_rect     = pygame.Rect(720, 395, 480, 65)
            self.load_rect     = pygame.Rect(720, 470, 480, 65)
            self.settings_rect = pygame.Rect(720, 545, 480, 65)
            self.mainmenu_rect = pygame.Rect(720, 620, 480, 65)
            self.quit_rect     = pygame.Rect(720, 695, 480, 65)

            buttons_list = [
                (self.continue_rect, get_text("POKRAČOVAT")),
                (self.save_rect,     get_text("ULOŽIT HRU")),
                (self.load_rect,     get_text("NAČÍST HRU")),
                (self.settings_rect, get_text("NASTAVENÍ")),
                (self.mainmenu_rect, get_text("NÁVRAT DO MENU")),
                (self.quit_rect,     get_text("UKONČIT HRU"))
            ]

            for rect, text in buttons_list:
                hovered = rect.collidepoint(get_mouse_pos())
                color = (65, 65, 110) if hovered else (30, 30, 55)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 215, 0), rect, 4)
                txt = self.font.render(text, True, (255, 255, 255))
                screen.blit(txt, txt.get_rect(center=rect.center))
            
            return
        
        if self.state == "TEAM_SELECT":
            screen.blit(self.font_big.render(get_text("VYBERTE SVŮJ TÝM"), True, (255, 215, 0)), (720, 120))
            for i, (team_name, team) in enumerate(self.teams.items()):
                rect = pygame.Rect(720, 180 + i*75, 520, 70)
                pygame.draw.rect(screen, team.color, rect)
                pygame.draw.rect(screen, (255,255,255), rect, 4)
                txt = self.font_big.render(team_name.upper(), True, (0,0,0))
                screen.blit(txt, txt.get_rect(center=rect.center))

        elif self.state == "SEASON_START":
            screen.blit(self.font_big.render(f"{get_text('Váš tým:')} {self.player_team.name}", True, self.player_team.color), (720, 300))
            self.start_season_button = pygame.Rect(760, 480, 400, 80)
            pygame.draw.rect(screen, (0, 180, 80), self.start_season_button)
            pygame.draw.rect(screen, (255,255,255), self.start_season_button, 4)
            txt = self.font_big.render(get_text("ZAČÁTEK SEZÓNY"), True, (255,255,255))
            screen.blit(txt, txt.get_rect(center=self.start_season_button.center))

        elif self.state == "RACE":
            if self.race_finished:
                self._draw_results_screen(screen)
                return

            # Horní informace - F1 styl
            current_lap = min(max((d.current_lap for d in self.drivers), default=0), self.current_track["laps"])
            track_name = self.current_track["name"] if self.current_track else "?"

            screen.blit(self.font_big.render(f"{get_text('Kolo')} {current_lap}/{self.current_track['laps']}", True, (255, 215, 0)), (40, 25))
            screen.blit(self.font.render(f"{get_text('Čas:')} {self.race_time:.1f}s", True, (255, 255, 255)), (40, 68))
            weather_text = (f"{get_text('Počasí:')} {get_text('WEATHER_' + self.current_weather)}   "
                            f"{get_text('Vlhkost trati:')} {int(self.track_wetness * 100)}%")
            screen.blit(self.font.render(weather_text, True, (100, 255, 255)), (40, 98))

            # Zobrazení fáze závodu
            if self.race_phase == RACE_PHASE_FORMATION:
                phase_text = self.font_big.render(get_text("FORMATION LAP"), True, (255, 100, 0))
                screen.blit(phase_text, (40, 130))
            elif self.race_phase == RACE_PHASE_START:
                phase_text = self.font_big.render(get_text("START LIGHTS"), True, (255, 60, 60))
                screen.blit(phase_text, (40, 130))
            elif self.start_lights_out_timer > 0:
                phase_text = self.font_big.render(get_text("LIGHTS OUT..."), True, (0, 255, 120))
                screen.blit(phase_text, (40, 130))

            # Název trati uprostřed
            screen.blit(self.font_big.render(track_name.upper(), True, (255, 215, 0)), 
                        self.font_big.render(track_name.upper(), True, (255, 215, 0)).get_rect(centerx=960, centery=45))
            
            # Zpráva o uložení / načtení
            if self.save_message_timer > 0:
                color = (0, 255, 140) if any(x in self.save_message.lower() for x in ["ulož", "načten"]) else (255, 100, 100)
                msg = self.font_big.render(self.save_message, True, color)
                screen.blit(msg, (960 - msg.get_width()//2, 520))

            # Vlajky
            if self.safety_car_active:
                screen.blit(self.font.render(get_text("FLAG_SC"), True, (255, 80, 0)), (1110, 30))
            elif self.vsc_active:
                screen.blit(self.font.render(get_text("FLAG_VSC"), True, (255, 200, 0)), (1110, 30))
            elif self.yellow_flag_active:
                screen.blit(self.font.render(get_text("FLAG_YELLOW"), True, (255, 255, 0)), (1110, 30))

                        # === LEADERBOARD VLEVO ===
            y = 170
            self.driver_rects = []

            # === BĚŽNÝ LEADERBOARD BĚHEM ZÁVODU ===
            # Stejný poziční vzorec jako jinde v kódu (handle_battles, Safety Car) -
            # dřív tu byly natvrdo konstanty *10000/*100, které by se rozbily na
            # trati s racing_line delší než 100 bodů (track_index by "přetekl" do
            # číslice kola).
            leaderboard_path_len = len(self.current_track["racing_line"])
            ordered = sorted(self.drivers,
                           key=lambda d: d.current_lap * leaderboard_path_len + d.track_index + d.progress,
                           reverse=True)
            
            leader_total_pos = (ordered[0].current_lap * leaderboard_path_len
                                + ordered[0].track_index + ordered[0].progress) if ordered else 0

            for i, driver in enumerate(ordered[:20]):
                rect = pygame.Rect(30, y, 460, 34)
                self.driver_rects.append((rect, driver))
                if driver == self.selected_driver:
                    pygame.draw.rect(screen, (70, 70, 100), rect)

                if driver.is_dnf:
                    gap_str = f"DNF ({get_text(driver.dnf_reason)})"
                    color = (200, 60, 60)
                elif driver.finished:
                    gap_str = f"({driver.total_time:.1f}s)"
                    color = (180, 180, 180)
                else:
                    # Rozestup podle skutečné pozice na trati, ne podle počítadla kol -
                    # jinak by po každém průjezdu lídra cílovou čárou (a hlavně na
                    # startu) všichni ostatní na chvíli svítili jako "+1 kolo".
                    gap_pts = max(0.0, leader_total_pos - (driver.current_lap * leaderboard_path_len
                                                           + driver.track_index + driver.progress))
                    if gap_pts < leaderboard_path_len:
                        gap_str = f"+{gap_pts * (88 / leaderboard_path_len):.1f}s"  # ~88s na kolo
                    else:
                        laps_down = int(gap_pts // leaderboard_path_len)
                        gap_str = f"+{laps_down} {get_text('LAP' if laps_down == 1 else 'LAPS')}"
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

                # Počasí přes mapu: ztmavení podle vlhkosti/oblačnosti + padající déšť
                dim = int(90 * self.track_wetness) + (25 if self.current_weather == "CLOUD" else 0)
                if dim > 0:
                    if self._weather_overlay is None or self._weather_overlay.get_size() != (map_w, map_h):
                        self._weather_overlay = pygame.Surface((map_w, map_h))
                        self._weather_overlay.fill((8, 16, 40))
                    self._weather_overlay.set_alpha(min(dim, 140))
                    screen.blit(self._weather_overlay, (map_x, map_y))
                if self.current_weather == "RAIN":
                    ticks = pygame.time.get_ticks()
                    for k in range(70):
                        rx = (k * 97 + ticks * 0.06) % map_w
                        ry = (k * 53 + ticks * 0.45) % map_h
                        pygame.draw.line(screen, (150, 170, 225),
                                         (map_x + rx, map_y + ry), (map_x + rx - 4, map_y + ry + 11), 1)

                # DRS zóny
                for start, end in self.current_track.get("drs_zones", []):
                    for i in range(start, min(end, len(path)-1)):
                        x1 = path[i][0] * scale_x + map_x
                        y1 = path[i][1] * scale_y + map_y
                        x2 = path[i+1][0] * scale_x + map_x
                        y2 = path[i+1][1] * scale_y + map_y
                        pygame.draw.line(screen, (0, 220, 255), (int(x1), int(y1)), (int(x2), int(y2)), 5)
                
                # Boxová ulička (odvozená z racing_line) + boxy týmů
                pit_geom = get_pit_geometry(self.current_track)
                lane_steps = int(pit_geom["length"] / 0.25)
                lane_points = []
                for step in range(lane_steps + 1):
                    px, py = pit_lane_position(self.current_track, pit_geom,
                                               pit_geom["entry"] + min(pit_geom["length"], step * 0.25))
                    lane_points.append((px * scale_x + map_x, py * scale_y + map_y))
                if len(lane_points) > 1:
                    pygame.draw.lines(screen, (255, 140, 0), False, lane_points, 3)
                team_list = list(self.teams.values())
                for team_i, team_obj in enumerate(team_list):
                    box_d = pit_box_distance(pit_geom, team_i, len(team_list), 0)
                    bx, by = pit_lane_position(self.current_track, pit_geom, pit_geom["entry"] + box_d, extra=9)
                    pygame.draw.rect(screen, team_obj.color,
                                     (int(bx * scale_x + map_x) - 3, int(by * scale_y + map_y) - 3, 6, 6))

                # Auta na trati
                for driver in self.drivers:
                    if driver.is_dnf or driver.finished: continue
                    if driver.in_pit:
                        px, py = pit_lane_position(self.current_track, pit_geom,
                                                   driver.track_index + driver.progress)
                        x = px * scale_x + map_x
                        y = py * scale_y + map_y
                    else:
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

                # === SAFETY CAR VIZUÁLNĚ ===
                if self.safety_car_active:
                    i = self.safety_car_index
                    next_i = (i + 1) % len(path)
                    x1, y1 = path[i]
                    x2, y2 = path[next_i]
                    x = x1 * scale_x + (x2 - x1) * self.safety_car_progress * scale_x + map_x
                    y = y1 * scale_y + (y2 - y1) * self.safety_car_progress * scale_y + map_y

                    # Velký žlutý kruh s černým okrajem
                    pygame.draw.circle(screen, (255, 215, 0), (int(x), int(y)), 14)      # žlutá
                    pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), 14, 4)       # černý okraj
                    pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), 8)           # vnitřní kruh

                    # Text "SC"
                    sc_text = self.font_small.render("SC", True, (0, 0, 0))
                    screen.blit(sc_text, sc_text.get_rect(center=(int(x), int(y))))

            # Startovní semafor (přes mapu)
            if self.race_phase == RACE_PHASE_START or self.start_lights_out_timer > 0:
                self._draw_start_lights(screen)

                        # === BOXY PRO JEZDCE 1 A 2 ===
            box_y = 650
            box_w = 380
            box_h = 95

            # Jezdec 1
            d1 = self.player_team.drivers[0]
            wear1 = int(d1.tire_wear * 100)

            box1_rect = pygame.Rect(480, box_y, box_w, box_h)
            pygame.draw.rect(screen, (30, 30, 40), box1_rect)
            pygame.draw.rect(screen, self.teams[d1.team_name].color, box1_rect, 4)

            screen.blit(self.font.render(f"1. {d1.name}", True, (255,255,255)), (500, box_y + 12))
            screen.blit(self.font.render(f"{get_text('Gumy:')} {d1.tire}", True, (255,215,0)), (500, box_y + 38))
            screen.blit(self.font_small.render(f"{get_text('Opotřebení kol:')} {wear1}%", True, (255,180,0)), (500, box_y + 68))

            # Tlačítko BOX
            self.pit_button1 = pygame.Rect(780, box_y + 18, 75, 60)
            pygame.draw.rect(screen, self._pit_button_color(d1), self.pit_button1)
            pygame.draw.rect(screen, (255,255,255), self.pit_button1, 3)
            screen.blit(self.font.render("BOX", True, (255,255,255)), 
                        self.font.render("BOX", True, (255,255,255)).get_rect(center=self.pit_button1.center))

            # Jezdec 2
            d2 = self.player_team.drivers[1]
            wear2 = int(d2.tire_wear * 100)

            box2_rect = pygame.Rect(880, box_y, box_w, box_h)
            pygame.draw.rect(screen, (30, 30, 40), box2_rect)
            pygame.draw.rect(screen, self.teams[d2.team_name].color, box2_rect, 4)

            screen.blit(self.font.render(f"2. {d2.name}", True, (255,255,255)), (900, box_y + 12))
            screen.blit(self.font.render(f"{get_text('Gumy:')} {d2.tire}", True, (255,215,0)), (900, box_y + 38))
            screen.blit(self.font_small.render(f"{get_text('Opotřebení kol:')} {wear2}%", True, (255,180,0)), (900, box_y + 68))

            # Tlačítko BOX
            self.pit_button2 = pygame.Rect(1180, box_y + 18, 75, 60)
            pygame.draw.rect(screen, self._pit_button_color(d2), self.pit_button2)
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
            screen.blit(self.font_big.render(get_text("TEAM STANDINGS"), True, (255, 255, 0)), (right_x - 240, 20))
            y = 70
            for i, team in enumerate(sorted(self.teams.values(), key=lambda t: t.points, reverse=True)[:10]):
                txt = self.font.render(f"{i+1}. {team.name}: {team.points} {get_text('PTS')}", True, team.color)
                screen.blit(txt, (right_x - 240, y))
                y += 28

            screen.blit(self.font_big.render(get_text("DRIVER STANDINGS"), True, (255, 220, 100)), (right_x - 240, y + 30))
            y += 60
            for i, driver in enumerate(sorted(self.drivers, key=lambda d: d.points, reverse=True)[:20]):
                color = self.teams.get(driver.team_name, (200,200,200)).color
                txt = self.font.render(f"{i+1}. {driver.name} — {driver.points} {get_text('PTS')}", True, color)
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

            # Zobrazení zprávy (uložení / načtení / seznam)
            if self.save_message_timer > 0:
                color = (0, 255, 120) if "uložena" in self.save_message.lower() or "načten" in self.save_message.lower() else (255, 200, 100)
                msg = self.font.render(self.save_message, True, color)
                screen.blit(msg, (960 - msg.get_width()//2, 520))

        elif self.state == "SAVE_LIST":
            screen.fill((12, 12, 22))
            title = self.font_big.render("ULOŽENÉ HRY", True, (255, 215, 0))
            screen.blit(title, title.get_rect(centerx=960, centery=80))

            if not self.save_list:
                text = self.font.render("Žádné uložené hry...", True, (200, 200, 200))
                screen.blit(text, text.get_rect(centerx=960, centery=300))
            else:
                for i, save in enumerate(self.save_list[:10]):
                    y = 160 + i * 58
                    rect = pygame.Rect(380, y, 1160, 52)
                    color = (80, 80, 140) if i == self.selected_save_index else (35, 35, 65)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (255, 215, 0), rect, 3)

                    date = save['date'][:16] if isinstance(save['date'], str) else "Neznámé"
                    line = f"{i+1:2}. {save['filename'][:50]:<50} | {save['track']} | Kolo {save['round']} | {date}"
                    txt = self.font.render(line, True, (255, 255, 255))
                    screen.blit(txt, (410, y + 14))

            help_text = self.font.render("↑↓ = výběr | ENTER = načíst | ESC = zpět", True, (180, 180, 180))
            screen.blit(help_text, help_text.get_rect(centerx=960, centery=780))

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
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 28)
        self.font_big = pygame.font.SysFont("arial", 42)
        self.font_small = pygame.font.SysFont("arial", 24)

        self.fps_options = [30, 60, 90, 120, 144, 240]
        self.current_fps_index = self.fps_options.index(CURRENT_FPS) if CURRENT_FPS in self.fps_options else 1

        self.fullscreen_rect = None
        self.fps_buttons = []
        self.race_mode_buttons = []
        self.language_buttons = []

        self.race_modes = ["SHORT", "FULL"]
        self.current_race_mode_index = 0 if CURRENT_RACE_MODE == "SHORT" else 1

        self.languages = ["ČEŠTINA", "ENGLISH", "ITALIANO"]
        if CURRENT_LANGUAGE == "CS":
            self.current_language_index = 0
        elif CURRENT_LANGUAGE == "EN":
            self.current_language_index = 1
        else:
            self.current_language_index = 2

        self.from_ingame = False
        self.race_screen = None  # rozjetý ChampionshipScreen, ke kterému se ESC vrátí

    def handle_events(self, events):
        global CURRENT_FPS, IS_FULLSCREEN, CURRENT_RACE_MODE, CURRENT_LANGUAGE

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.from_ingame:
                        change_screen(GAME_STATE_RACE)
                    else:
                        change_screen(GAME_STATE_MENU)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = get_mouse_pos()

                if self.fullscreen_rect and self.fullscreen_rect.collidepoint(pos):
                    toggle_fullscreen()

                for i, btn in enumerate(self.fps_buttons):
                    if btn.collidepoint(pos):
                        self.current_fps_index = i
                        CURRENT_FPS = self.fps_options[i]

                for i, rect in enumerate(self.race_mode_buttons):
                    if rect.collidepoint(pos):
                        self.current_race_mode_index = i
                        CURRENT_RACE_MODE = self.race_modes[i]

                for i, rect in enumerate(self.language_buttons):
                    if rect.collidepoint(pos):
                        self.current_language_index = i
                        if i == 0:
                            CURRENT_LANGUAGE = "CS"
                        elif i == 1:
                            CURRENT_LANGUAGE = "EN"
                        else:
                            CURRENT_LANGUAGE = "IT"   # Italian
                        print(f"Jazyk: {CURRENT_LANGUAGE}")

                print(f"Jazyk změněn na: {CURRENT_LANGUAGE}")
                # Refresh aktuální obrazovky
                if isinstance(current_screen, MenuScreen) or isinstance(current_screen, ChampionshipScreen):
                    pass  # při příštím draw se použije nový jazyk

    def draw(self, screen):
        screen.fill((12, 12, 25))

        title = self.font_big.render(get_text("NASTAVENÍ"), True, (255, 215, 0))
        screen.blit(title, title.get_rect(centerx=960, centery=120))

        # FPS
        fps_title = self.font.render(get_text("FRAMERATE (FPS)"), True, (200, 200, 220))
        screen.blit(fps_title, (580, 200))
        self.fps_buttons = []
        for i, fps in enumerate(self.fps_options):
            x = 580 + i * 110
            rect = pygame.Rect(x, 250, 95, 55)
            self.fps_buttons.append(rect)
            color = (255, 215, 0) if fps == CURRENT_FPS else (40, 40, 60)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 4 if fps == CURRENT_FPS else 2)
            txt = self.font.render(str(fps), True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))

        # Race Mode
        mode_title = self.font.render(get_text("DÉLKA ZÁVODU"), True, (200, 200, 220))
        screen.blit(mode_title, (580, 340))
        self.race_mode_buttons = []
        for i, mode in enumerate(self.race_modes):
            x = 580 + i * 320
            rect = pygame.Rect(x, 390, 280, 60)
            self.race_mode_buttons.append(rect)
            color = (255, 215, 0) if i == self.current_race_mode_index else (40, 40, 60)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 4 if i == self.current_race_mode_index else 2)
            txt_text = "SHORT RACE" if mode == "SHORT" else "FULL RACE (1h30+)"
            txt = self.font.render(txt_text, True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))

        # Language
        lang_title = self.font.render(get_text("JAZYK"), True, (200, 200, 220))
        screen.blit(lang_title, (580, 480))
        self.language_buttons = []
        for i, lang in enumerate(self.languages):
            x = 580 + i * 320
            rect = pygame.Rect(x, 530, 280, 60)
            self.language_buttons.append(rect)
            color = (255, 215, 0) if i == self.current_language_index else (40, 40, 60)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 4 if i == self.current_language_index else 2)
            txt = self.font.render(lang, True, (255,255,255))
            screen.blit(txt, txt.get_rect(center=rect.center))

        back = self.font_small.render("ESC = zpět", True, (160, 160, 180))
        screen.blit(back, (780, 720))

def change_screen(new_state):
    global current_screen, game_state

    # Musí se zjistit PŘED přepsáním current_screen na nový screen - jinak nejde
    # poznat, odkud přechod přišel (dřív se to kontrolovalo až po přepsání, takže
    # podmínka byla vždy False a "návrat z Nastavení" vždy založil úplně nový,
    # prázdný ChampionshipScreen a rozjetý závod se tím nenávratně zahodil).
    previous_screen = current_screen

    game_state = new_state

    if new_state == GAME_STATE_MENU:
        current_screen = MenuScreen()

    elif new_state == GAME_STATE_RACE:
        # Návrat z Nastavení do právě probíhajícího závodu - použít existující
        # ChampionshipScreen, ne založit nový (to by zahodilo celý rozjetý závod).
        resumed_race = previous_screen.race_screen if isinstance(previous_screen, SettingsScreen) else None
        if resumed_race is not None:
            current_screen = resumed_race
            current_screen.show_ingame_menu = False
            current_screen.paused = False
            current_screen.state = "RACE"
        else:
            current_screen = ChampionshipScreen()

    elif new_state == GAME_STATE_PRACTICE:
        current_screen = PracticeScreen()

    elif new_state == GAME_STATE_SETTINGS:
        current_screen = SettingsScreen()
        # Pokud přicházíme z rozjetého závodu, uložit si ho, aby na ESC šlo vrátit
        if isinstance(previous_screen, ChampionshipScreen):
            current_screen.race_screen = previous_screen
            current_screen.from_ingame = True
        
change_screen(GAME_STATE_MENU)

# vykreslovaci smycka / main loop
while True:
    delta_time = clock.tick(CURRENT_FPS) / 1000
    events = pygame.event.get()
    
    # kontrola vypnutí hry
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            toggle_fullscreen()   # F11 = celá obrazovka / okno
    
    current_screen.handle_events(events)
    current_screen.update(delta_time)
    
    screen.fill((20,20,20))

    current_screen.draw(screen)

    present_frame()