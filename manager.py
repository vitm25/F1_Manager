import pygame
import math
import sys
pygame.init() # spusteni knihovny

rozliseni_okna = (1000, 800)
barvy_pozadi = (0, 0, 0,)
FPS = 60

#vykreslení okna
okno = pygame.display.set_mode(rozliseni_okna)
pygame.display.set_caption("F1 manažer")

clock = pygame.time.Clock()

GAME_STATE_RACE = "RACE"
game_state = GAME_STATE_RACE

race_time = 0.0

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
