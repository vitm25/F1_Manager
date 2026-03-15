import pygame
import sys
import os
import math

pygame.init()

WIDTH = 1920
HEIGHT = 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Line Editor v2")

clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)

# =========================================================
# NASTAVENÍ
# =========================================================
TRACK_IMAGE_PATH = "tracks/usavegas.png"
OUTPUT_FILE = "racing_lines/las_vegas.py"

DISPLAY_WIDTH = 1000
DISPLAY_HEIGHT = 1000

BG_COLOR = (20, 20, 20)
LINE_COLOR = (255, 0, 0)
PIT_COLOR = (255, 140, 0)
DRS_COLOR = (0, 200, 255)
SECTOR_COLOR = (255, 255, 0)
POINT_COLOR = (0, 255, 255)
TEXT_COLOR = (255, 255, 255)

MODE_LINE = "LINE"
MODE_PIT = "PIT"
MODE_DRS = "DRS"
MODE_SECTOR = "SECTOR"

mode = MODE_LINE

# =========================================================
# DATA
# =========================================================
racing_line = []
pit_lane = []

# více DRS zón
drs_zones = []
current_drs_start = None

# 2 body -> 3 sektory
sector_points = []

# =========================================================
# LOAD TRACK
# =========================================================
track_image_original = pygame.image.load(TRACK_IMAGE_PATH)
track_image = pygame.transform.scale(track_image_original, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
track_rect = track_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# =========================================================
# FUNKCE
# =========================================================
def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def get_relative_points(points):
    """Uloží body relativně k obrázku tratě."""
    relative = []
    for x, y in points:
        relative.append((int(x - track_rect.x), int(y - track_rect.y)))
    return relative

def save_track_data():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    relative_racing_line = get_relative_points(racing_line)
    relative_pit_lane = get_relative_points(pit_lane)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("track_data = {\n")

        f.write('    "racing_line": [\n')
        for x, y in relative_racing_line:
            f.write(f"        ({x}, {y}),\n")
        f.write("    ],\n")

        f.write(f'    "drs_zones": {drs_zones},\n')

        f.write('    "pit_lane": [\n')
        for x, y in relative_pit_lane:
            f.write(f"        ({x}, {y}),\n")
        f.write("    ],\n")

        f.write(f'    "sector_points": {sector_points},\n')

        f.write("}\n")

    print(f"Uloženo do: {OUTPUT_FILE}")

def auto_close_line(points):
    if len(points) >= 3 and points[0] != points[-1]:
        points.append(points[0])

def smooth_line(points, closed=False, iterations=1):
    if len(points) < 3:
        return points[:]

    result = points[:]

    for _ in range(iterations):
        new_points = []

        work_points = result[:]
        if closed and work_points[0] != work_points[-1]:
            work_points.append(work_points[0])

        for i in range(len(work_points) - 1):
            x1, y1 = work_points[i]
            x2, y2 = work_points[i + 1]

            qx = 0.75 * x1 + 0.25 * x2
            qy = 0.75 * y1 + 0.25 * y2

            rx = 0.25 * x1 + 0.75 * x2
            ry = 0.25 * y1 + 0.75 * y2

            new_points.append((qx, qy))
            new_points.append((rx, ry))

        if closed:
            if len(new_points) > 0 and new_points[0] != new_points[-1]:
                new_points.append(new_points[0])

        result = [(int(x), int(y)) for x, y in new_points]

    return result

def find_nearest_point_index(mouse_pos, points, max_dist=20):
    nearest_index = None
    nearest_dist = max_dist

    for i, p in enumerate(points):
        d = distance(mouse_pos, p)
        if d < nearest_dist:
            nearest_dist = d
            nearest_index = i

    return nearest_index

def draw_points(points, color, show_index=True, radius=5):
    for i, p in enumerate(points):
        pygame.draw.circle(screen, color, p, radius)
        if show_index:
            label = small_font.render(str(i), True, TEXT_COLOR)
            screen.blit(label, (p[0] + 6, p[1] - 6))

def draw_polyline(points, color, closed=False, width=3):
    if len(points) > 1:
        pygame.draw.lines(screen, color, closed, points, width)

def draw_drs_zones():
    if len(racing_line) < 2:
        return

    for start, end in drs_zones:
        if start >= len(racing_line) or end >= len(racing_line):
            continue

        a = min(start, end)
        b = max(start, end)

        for i in range(a, min(b, len(racing_line) - 1)):
            pygame.draw.line(screen, DRS_COLOR, racing_line[i], racing_line[i + 1], 6)

    # rozkliknutý začátek další DRS zóny
    if current_drs_start is not None and 0 <= current_drs_start < len(racing_line):
        pygame.draw.circle(screen, (255, 255, 255), racing_line[current_drs_start], 10, 2)

def draw_sector_markers():
    for idx in sector_points:
        if 0 <= idx < len(racing_line):
            pygame.draw.circle(screen, SECTOR_COLOR, racing_line[idx], 10, 2)

def clear_current_mode():
    global racing_line, pit_lane, drs_zones, current_drs_start, sector_points

    if mode == MODE_LINE:
        racing_line = []
        drs_zones = []
        current_drs_start = None
        sector_points = []
    elif mode == MODE_PIT:
        pit_lane = []
    elif mode == MODE_DRS:
        drs_zones = []
        current_drs_start = None
    elif mode == MODE_SECTOR:
        sector_points = []

def draw_ui():
    info_lines = [
        f"Mode: {mode}",
        "",
        "1 = Racing line mode",
        "2 = Pit lane mode",
        "3 = DRS zones mode",
        "4 = Sector points mode",
        "",
        "LMB = Add/select point",
        "Backspace = Remove last point",
        "D = Remove last DRS zone",
        "C = Clear current mode",
        "U = Auto-close racing line",
        "G = Smooth racing line",
        "S = Save to file",
        "ESC = Exit",
        "",
        f"Racing points: {len(racing_line)}",
        f"Pit points: {len(pit_lane)}",
        f"DRS zones: {drs_zones}",
        f"Current DRS start: {current_drs_start}",
        f"Sector points: {sector_points}",
        "",
        "Pozn.: 2 sektorové body = 3 sektory",
    ]

    panel_x = 20
    panel_y = 20

    for line in info_lines:
        text = font.render(line, True, TEXT_COLOR)
        screen.blit(text, (panel_x, panel_y))
        panel_y += 30

def handle_click(mouse_pos):
    global current_drs_start, drs_zones, sector_points

    if not track_rect.collidepoint(mouse_pos):
        return

    if mode == MODE_LINE:
        racing_line.append(mouse_pos)

    elif mode == MODE_PIT:
        pit_lane.append(mouse_pos)

    elif mode == MODE_DRS:
        idx = find_nearest_point_index(mouse_pos, racing_line)
        if idx is not None:
            if current_drs_start is None:
                current_drs_start = idx
            else:
                drs_zones.append((current_drs_start, idx))
                current_drs_start = None

    elif mode == MODE_SECTOR:
        idx = find_nearest_point_index(mouse_pos, racing_line)
        if idx is not None:
            if len(sector_points) < 2:
                sector_points.append(idx)
                sector_points.sort()
            else:
                sector_points = [idx]

# =========================================================
# MAIN LOOP
# =========================================================
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_1:
                mode = MODE_LINE

            elif event.key == pygame.K_2:
                mode = MODE_PIT

            elif event.key == pygame.K_3:
                mode = MODE_DRS

            elif event.key == pygame.K_4:
                mode = MODE_SECTOR

            elif event.key == pygame.K_BACKSPACE:
                if mode == MODE_LINE and racing_line:
                    racing_line.pop()
                elif mode == MODE_PIT and pit_lane:
                    pit_lane.pop()
                elif mode == MODE_SECTOR and sector_points:
                    sector_points.pop()

            elif event.key == pygame.K_d:
                if mode == MODE_DRS and drs_zones:
                    drs_zones.pop()

            elif event.key == pygame.K_c:
                clear_current_mode()

            elif event.key == pygame.K_u:
                auto_close_line(racing_line)

            elif event.key == pygame.K_g:
                closed = len(racing_line) > 2 and racing_line[0] == racing_line[-1]
                racing_line = smooth_line(racing_line, closed=closed, iterations=1)

            elif event.key == pygame.K_s:
                save_track_data()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                handle_click(event.pos)

    # draw
    screen.fill(BG_COLOR)
    screen.blit(track_image, track_rect.topleft)

    draw_drs_zones()
    draw_polyline(racing_line, LINE_COLOR, closed=False, width=3)
    draw_points(racing_line, POINT_COLOR, show_index=True, radius=4)

    draw_polyline(pit_lane, PIT_COLOR, closed=False, width=3)
    draw_points(pit_lane, PIT_COLOR, show_index=False, radius=4)

    draw_sector_markers()
    draw_ui()

    pygame.display.flip()

pygame.quit()
sys.exit()