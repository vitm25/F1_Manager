import pygame
import math
import sys
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

class Driver:
    def __init__(self, name):
        self.name = name
        self.lap_time = 3.0
        self.current_lap = 0
        self.total_time = 0.0
        self.lap_timer = 0.0

drivers = [
    Driver("Driver A"),
    Driver("Driver B"),
    Driver("Driver C"),
    Driver("Driver D"),
    Driver("Driver E"),
    Driver("Driver F"),
    ]
           
lap_timer = 0.0

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
            d.lap_timer += delta_time
            
            if d.lap_timer >= d.lap_time:
                d.lap_timer -= d.lap_time
                d.current_lap += 1
                d.total_time += d.lap_time
                print(f"{d.name} completed lap {d.current_lap}")
                
        
    #draw
    screen.fill((20,20,20,))
    
    time_text = font.render(f"Race time: {race_time:.1f}s", True, (255,255,255))
    screen.blit(time_text, (20,20))
    
    
    y = 60
    for d in drivers:
        text = font.render(
            f"{d.name} | Lap: {d.current_lap} | Time: {d.total_time:.1f}s",
            True,
            (200,200,200)
        )
        screen.blit(text, (20, y))
        y += 30
    
    pygame.display.flip()
    
    