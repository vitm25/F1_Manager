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
    def _init_(self, name):
        self.name = name
        self. lap_time = 90.0
        

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
            
    if game_state == GAME_STATE_RACE:
        race_time += delta_time
        
    #draw
    screen.fill((20,20,20,))
    
    time_text = font.render(f"Race time: {race_time:.1f}s", True, (255,255,255))
    screen.blit(time_text, (20,20))
    
    pygame.display.flip()
    
        
    

    
