import pygame
import sys
import os

pygame.init()

WIDTH = 1920
HEIGHT = 1080

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Line Editor")

font = pygame.font.SysFont("arial", 28)
clock = pygame.time.Clock()

# =========================
# NASTAVENÍ
# =========================
TRACK_IMAGE_PATH = "tracks/usavegas.png"
OUTPUT_FILE = "racing_lines/usavegas.py"

track_image = pygame.image.load(TRACK_IMAGE_PATH)
track_rect = track_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))

points = []

def save_racing_line(points, output_file, track_rect):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # uložíme body relativně k obrázku tratě
    relative_points = []
    for x, y in points:
        relative_points.append((x - track_rect.x, y - track_rect.y))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("racing_line = [\n")
        for x, y in relative_points:
            f.write(f"    ({x}, {y}),\n")
        f.write("]\n")

    print(f"Uloženo do: {output_file}")


running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_BACKSPACE:
                if points:
                    points.pop()

            elif event.key == pygame.K_c:
                points.clear()

            elif event.key == pygame.K_s:
                save_racing_line(points, OUTPUT_FILE, track_rect)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # levé tlačítko
                mx, my = event.pos

                # přidáme bod jen když klikneš do oblasti obrázku
                if track_rect.collidepoint(mx, my):
                    points.append((mx, my))

    screen.fill((20, 20, 20))
    screen.blit(track_image, track_rect.topleft)

    # spojnice mezi body
    if len(points) > 1:
        pygame.draw.lines(screen, (0, 200, 255), False, points, 3)

    # body
    for i, point in enumerate(points):
        pygame.draw.circle(screen, (255, 0, 0), point, 6)

        label = font.render(str(i), True, (255, 255, 255))
        screen.blit(label, (point[0] + 8, point[1] - 8))

    info_lines = [
        "Levé tlačítko myši = přidat bod",
        "Backspace = smazat poslední bod",
        "C = vyčistit vše",
        "S = uložit racing_line.py",
        "ESC = konec",
        f"Počet bodů: {len(points)}",
    ]

    y = 20
    for line in info_lines:
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (20, y))
        y += 35

    pygame.display.flip()

pygame.quit()
sys.exit()