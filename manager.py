import pygame
import math
import sys
pygame.init() # spusteni knihovny

rozliseni_okna = (1000, 800)
barvy_pozadi = (0, 0, 0,)

#vykreslení okna
okno = pygame.display.set_mode(rozliseni_okna)
pygame.display.set_caption("F1 manažér")

# vykreslovaci smycka
while True:
    # kontrola probehlych udalosti
    for udalost in pygame.event.get():
        # kontrola udalosti "vypnout"
        if udalost.type == pygame.QUIT:
            # vypnuti knihovny
            pygame.quit()
            # vypnuti programu
            sys.exit()

