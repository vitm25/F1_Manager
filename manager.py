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
screen = pygame.display.set_mode(rozliseni_okna)
pygame.display.set_caption("F1 manažer")

clock = pygame.time.Clock()

GAME_STATE_RACE = "RACE"
game_state = GAME_STATE_RACE

current_weather = "SUN"
weather_timer = 0.0
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

drivers = [
    Driver("Driver A", 3.0, "SOFT"),
    Driver("Driver B", 3.1, "MEDIUM"),
    Driver("Driver C", 3.2, "HARD"),
    ]
           
PIT_TIME = 5.0
selected_driver = drivers[0]

#safety car/ VSC/ red flag
safety_car_active = False
safety_car_timer = 0.0
SAFETY_CAR_DURATION = 8.0

vsc_active = False
vsc_timer = 0.0
VSC_DURATION = 6.0

red_flag_active = False
red_flag_timer = 0.0
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
    results = sorted(drivers, key=lambda d:total_time)
    
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
        d.toral_time = 0
        d.current_lap = 0
        d.tire_wear = 0
        d.in_pit = False
        d.finished = False

# vykreslovaci smycka
while True:
    delta_time = clock.tick(FPS) / 1000
    # kontrola probehlych udalosti
    for event in pygame.event.get():
        # kontrola udalosti "vypnout"
        if event.type == pygame.QUIT:
            # vypnuti knihovny
            pygame.quit()
            # vypnuti programu
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                driver = selected_driver # vybírání jezdce
                driver.pit_error = random.random() < 0.15 # chyba při vjezdu do boxu
                
                # pitstopy
                can_pit = (
                    not driver.in_pit and driver.current_lap - driver.last_pit_lap >= driver.pit_cooldown_laps
                )
                
                if can_pit:
                    driver.in_pit = True
                    driver.pit_timer = 0.0
                    print(f"{driver.name} entering pit lane")
                else:
                    print(f"{driver.name} cannot pit yet")
            
            if event.key == pygame.K_UP: # výběr jezdce nahoru
                idx = drivers.index(selected_driver)
                idx -= 1
                if idx < 0:
                    idx = len(drivers) - 1
                selected_driver = drivers[idx]
                    
            if event.key == pygame.K_DOWN: # výběr jezdce dolu
                idx = drivers.index(selected_driver)
                idx += 1
                if idx >= len(drivers):
                    idx = 0
                selected_driver = drivers[idx]
            # výběr pneu    
            if event.key == pygame.K_1:
                selected_driver.next_tire = "SOFT"
                print(f"{selected_driver.name} selected SOFT")
                
            if event.key == pygame.K_2:
                selected_driver.next_tire = "MEDIUM"
                print(f"{selected_driver.name} selected MEDIUM")
                
            if event.key == pygame.K_3:
                selected_driver.next_tire = "HARD"
                print(f"{selected_driver.name} selected HARD")
            
            if event.key == pygame.K_4:
                selected_driver.next_tire = "INTER"
                print(f"{selected_driver.name} selected INTER")
            
            if event.key == pygame.K_5:
                selected_driver.next_tire = "WET"
                print(f"{selected_driver.name} selected WET")
            # další závod
            if event.key == pygame.K_n:
                reset_race(drivers)
                print("Next race started!")
            
# update
    if game_state == "FINISHED":
        continue

    if red_flag_active:
        red_flag_timer += delta_time
        
        if red_flag_timer >= RED_FLAG_DURATION:
            red_flag_active = False
            print("🟢 RACE RESTART")
            
            for d in drivers:
                d.tire = "MEDIUM"
                d.next_tire = "MEDIUM"
                d.tire_wear = 0.0
        
        continue 
    
    # red flag
    if not safety_car_active and not vsc_active and not red_flag_active:
        if random.random() < 0.0005:
            red_flag_active = True
            red_flag_timer = 0.0
            print("🔴 RED FLAG")
    
    # VSC
    if not safety_car_active and not vsc_active and not red_flag_active:
        if random.random() < 0.0015:
            vsc_active = True
            vsc_timer = 0.0
            print("🟣 VIRTUAL SAFETY CAR")
    
    #safety car
    if not safety_car_active:
        if random.random() < 0.001:
            safety_car_active = True
            safety_car_timer = 0.0
            print("🚨 SAFETY CAR DEPLOYED")
    
    if game_state == GAME_STATE_RACE:
        race_time += delta_time
        
        for d in drivers:
            
            # pit stop
            if d.in_pit:
                d.pit_timer += delta_time

                required_pit_time = PIT_TIME
                if safety_car_active:
                    required_pit_time -= 2.0
                if vsc_active:
                    required_pit_time -= 1.0
                
                if d.pit_error:
                    required_pit_time += 2.0
                    
                if d.pit_timer >= required_pit_time:
                    d.in_pit = False
                    d.tire = d.next_tire
                    d.tire_wear = 0.0
                    d.pit_timer = 0.0
                    d.last_pit_lap = d.current_lap
                    d.pit_error = False
                    print(f"{d.name} pit stop completed")

                continue
            
            if safety_car_active:
                safety_car_timer += delta_time
                
                if safety_car_timer >= SAFETY_CAR_DURATION:
                    safety_car_active = False
                    print("🟢 SAFETY CAR IN THIS LAP")
                    
            if vsc_active:
                vsc_timer += delta_time
                if vsc_timer >= VSC_DURATION:
                    vsc_active = False
                    print("🟢 VSC ENDING")
                    
            #spuštění AI rozhodnutí
            if d != selected_driver:
                if ai_should_pit(d):
                    d.in_pit = True
                    d.pit_timer = 0.0
                    d.next_tire = ai_choose_tire(d)
                    print(f"🤖 {d.name} pits for {d.next_tire}")
                    
            #počasí
            weather_timer += delta_time
            
            if weather_timer >= WEATHER_CHANGE_TIME:
                weather_timer = 0.0
                
                roll = random.random()
                if roll < 0.6:
                    current_weather = "SUN"
                elif roll < 0.85:
                    current_weather = "CLOUD"
                else:
                    current_weather = "RAIN"
                    
                print(f"Weather changed to {current_weather}")
            
            # normal lap / výpočet kola
            d.lap_timer += delta_time
            
            tire_data = TIRES[d.tire]
            degradation = d.tire_wear * 0.5
            if d.tire_wear > 0.7:
                degradation += 0.3
                
            if d.tire_wear > 0.9:
                if random.random() < 0.02:
                    print(f"⚠️ {d.name} tyre issue!")
                    d.total_time += 2.0
            
            variation = random.uniform(-0.1, 0.1)
            
            weather_data = WEATHER_TYPES[current_weather]
            
            current_lap_time = (
                d.base_lap_time +
                tire_data["pace"] +
                degradation +
                variation +
                weather_data["lap_modifier"]
            )
            
            #penalizace za špatné pneumatiky
            if current_weather == "RAIN":
                if d.tire in ["SOFT", "MEDIUM", "HARD"]:
                    current_lap_time += 2.5
            elif current_weather == "SUN":
                if d.tire in ["INTER", "WET"]:
                    current_lap_time += 1.5
                    
            #riziko nehod
            if current_weather == "RAIN":
                if d.tire in ["SOFT", "MEDIUM", "HARD"]:
                    if random.random() < 0.01:
                        print(f" {d.name} crashed on slicks in rain!")
                        d.total_time +=2.0
            
            if d.lap_timer >= current_lap_time:
                d.lap_timer -= current_lap_time
                d.current_lap += 1
                d.total_time += current_lap_time
                d.tire_wear += tire_data["wear"] * weather_data["wear_modifier"]
                
            current_lap_time = (
                d.base_lap_time +
                tire_data["pace"] +
                degradation +
                variation
            )
            
            if safety_car_active:
                current_lap_time += 1.5
                
            if vsc_active:
                current_lap_time += 0.8
                
        leader = max(drivers, key=lambda d: d.current_lap)
        
        if d.current_lap >= RACE_LAPS:
            race_finished = True
            
        if race_finished and not points_awarded:        
            # pořadí
            drivers.sort(key=lambda d: (-d.current_lap, d.total_time))
            # body
            for i, d in enumerate(drivers):
                if i < len(POINTS):
                    d.points += POINTS[i]
                    
            print("🏁 RACE FINISHED")
            for d in drivers:
                print(f"{d.name}: {d.points} pts")
                
            points_awarded = True
            game_state = "FINISHED"
            
            # body do šampionátu
        if race_finished and not points_awarded:
            award_championship_points(drivers)
            points_awarded = True
            
    # draw
    screen.fill((20,20,20,))
    pygame.draw.line(screen, (80, 80, 80), (680,0), (680,600), 2)
    
        #safety car
    if safety_car_active:
        sc_text = font.render("SAFETY CAR DEPLOYED", True, (255, 255, 0))
        screen.blit(sc_text, (350, 20))
        
        # VSC
    if vsc_active:
        vsc_text = font.render("VIRTUAL SAFETY CAR", True, (200, 0, 255))
        screen.blit(vsc_text, (350, 50))
        
        # red flag
    if red_flag_active:
        rf_text = font.render("RED FLAG", True, (255, 0, 0))
        screen.blit(rf_text, (350, 80))
    
        # čas závodu
    time_text = font.render(f"Race time: {race_time:.1f}s", True, (255,255,255))
    screen.blit(time_text, (20,20))
    
        #počasí
    if current_weather == "SUN":
        weather_color = (255, 255, 0)
    elif current_weather == "CLOUD":
        weather_color = (180, 180, 180)
    else:
        weather_color = (100, 150, 255)
    
    weather_text = font.render(f"Weather: {current_weather}", True, weather_color)
    screen.blit(weather_text, (20,45))
    
        # jezdci
    y = 60
    for i,d in enumerate(drivers):
        
        if d.in_pit:
            status = f"PIT → {d.next_tire}"
        else:
            status = d.tire
            
        is_selected = (d == selected_driver)
        
        ai_mark = "🤖" if d != selected_driver else ""
        
        #barvičky
        color = (0, 255, 0) if is_selected else ((255, 200, 100) if d.in_pit else (200,200,200))
        if d.tire_wear > 0.9:
            color = (255, 50, 50)
        elif d.tire_wear > 0.7:
            color = (255, 150, 50)
        
        cooldown_left = max(0, d.pit_cooldown_laps - (d.current_lap - d.last_pit_lap))
        
        #jezdec
        text = font.render(
            f"P{i} {d.name} | {status} | L{d.current_lap} | {d.total_time:.1f}s | {d.points}pts",
            True,
            color
        )
        screen.blit(text, (20, y))
        y += 30
        
        #race finished
        if game_state == "FINISHED":
            end_text = font.render("RACE FINISHED", True, (0, 255, 0))
            screen.blit(end_text, (400, 300))
            
        # šampionát
        championship = sorted(drivers, key=lambda d: d.points, reverse=True )
        
        y = 120
        title = font.render("CHAMPIONSHIP", True, (255, 255, 255))
        CHAMP_X = 700
        
        screen.blit(title, (CHAMP_X, 80))
        
        for i, d in enumerate(championship):
            text = font.render(f"{i+1}. {d.name} - {d.points} pts", True, (255, 255, 255))
        screen.blit(text, (CHAMP_X, y))
        y += 25
    
    pygame.display.flip()