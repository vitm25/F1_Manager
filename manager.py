import pygame
import math
import sys
import random
pygame.init() # spusteni knihovny

rozliseni_okna = (1000, 600)
barvy_pozadi = (0, 0, 0,)
FPS = 60

#vykreslení okna
screen = pygame.display.set_mode(rozliseni_okna)
pygame.display.set_caption("F1 manažer")

clock = pygame.time.Clock()

GAME_STATE_RACE = "RACE"
game_state = GAME_STATE_RACE

race_time = 0.0
font = pygame.font.SysFont(None, 36)

TIRES = {
    "SOFT": {"pace": -0.3, "wear": 0.04},
    "MEDIUM": {"pace": 0.0, "wear": 0.025},
    "HARD": {"pace": 0.3, "wear": 0.015}
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

drivers = [
    Driver("Driver A", 3.0, "SOFT"),
    Driver("Driver B", 3.1, "MEDIUM"),
    Driver("Driver C", 3.2, "HARD"),
    ]
           
PIT_TIME = 5.0
selected_driver = drivers[0]

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
                
            
            
    # update
    if game_state == GAME_STATE_RACE:
        race_time += delta_time
        
        for d in drivers:
            
            # pit stop
            if d.in_pit:
                d.pit_timer += delta_time

                required_pit_time = PIT_TIME
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
            
            current_lap_time = (
                d.base_lap_time +
                tire_data["pace"] +
                degradation +
                variation
            )
            
            if d.lap_timer >= current_lap_time:
                d.lap_timer -= current_lap_time
                d.current_lap += 1
                d.total_time += current_lap_time
                d.tire_wear += tire_data["wear"]
                
        # pořadí
        drivers.sort(key=lambda d: (-d.current_lap, d.total_time))
            
    # draw
    screen.fill((20,20,20,))
    
        # čas závodu
    time_text = font.render(f"Race time: {race_time:.1f}s", True, (255,255,255))
    screen.blit(time_text, (20,20))
    
        # jezdci
    y = 60
    for i,d in enumerate(drivers):
        
        if d.in_pit:
            status = f"PIT → {d.next_tire}"
        else:
            status = d.tire
            
        is_selected = (d == selected_driver)
        
        color = (0, 255, 0) if is_selected else (
            (255, 200, 100) if d.in_pit else (200,200,200))
        if d.tire_wear > 0.9:
            color = (255, 50, 50)
        elif d.tire_wear > 0.7:
            color = (255, 150, 50)
        
        cooldown_left = max(0, d.pit_cooldown_laps - (d.current_lap - d.last_pit_lap))
        
        text = font.render(
            f"P{i+1} | {d.name} | {status} | {d.tire} | Wear: {int(d.tire_wear*100)}% Lap: {d.current_lap} | Time: {d.total_time:.1f}s | Cooldown: {cooldown_left}",
            True,
            color
        )
        screen.blit(text, (20, y))
        y += 30
    
    pygame.display.flip()
    
