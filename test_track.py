import pygame

pygame.init()

screen = pygame.display.set_mode((1920,1080))
pygame.display.set_caption("F1 Track Test")

track = pygame.image.load("changing_png/usacota.png")

track = pygame.transform.scale(track,(1080,1080))

x = (1920 - 1080) // 2
y = (1080 - 1080) // 2

running = True 
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30,30,30))
    screen.blit(track,(x,y))

    pygame.display.update()

pygame.quit()