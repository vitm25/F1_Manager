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

class Driver:
    def __init__(self, name, base_lap_time, tire):
        self.name = name
        self.base_lap_time = base_lap_time
        self.tire = tire
        self.tire_wear = 0.0
        
        self.current_lap = 0
        self.total_time = 0.0
        self.lap_timer = 0.0
        
        self.in_pit = False
        self.pit_timer = 0.0

drivers = [
    Driver("Driver A", 3.0, "SOFT"),
    Driver("Driver B", 3.1, "MEDIUM"),
    Driver("Driver C", 3.2, "HARD"),
]
           
lap_timer = 0.0
PIT_TIME = 5.0

# vykreslovaci smycka
while True:
    delta_time = clock.tick(FPS) / 1000
    # kontrola probehlych udalosti
    for udalost in pygame.event.get():
        # kontrola udalosti "vypnout"
        if udalost.type == pygame.QUIT:
            # vypnuti knihovny
            pygame.quit()
            # vypnuti programu
            sys.exit()
            
    #update
    if game_state == GAME_STATE_RACE:
        race_time += delta_time
        
        for d in drivers:
            drivers.sort(
                key=lambda d: (-d.current_lap, d.total_time)
            )
            d.lap_timer += delta_time
            
            tire_data = TIRES[d.tire]
            
            degradation = d.tire_wear * 0.5
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
                
    #eventy
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_p:
            driver = drivers[0] #zatím jen první jezdec
                
                
        
    #draw
    screen.fill((20,20,20,))
    
    time_text = font.render(f"Race time: {race_time:.1f}s", True, (255,255,255))
    screen.blit(time_text, (20,20))
    
    
    y = 60
    for i,d in enumerate(drivers, start=1):
        text = font.render(
            f"P{i} | {d.name} | {d.tire} | Wear: {int(d.tire_wear*100)}% Lap: {d.current_lap} | Time: {d.total_time:.1f}s",
            True,
            (200,200,200)
        )
        screen.blit(text, (20, y))
        y += 30
    
    pygame.display.flip()
    
    