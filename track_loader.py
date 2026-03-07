import pygame

def load_track_points(image_path):
    
    img = pygame.image.load(image_path)
    width, height = img.get_size()
    
    points = []
    
    for x in range(width):
        for y in range(height):
            
            color = img.get_at((x,y))
            
            #