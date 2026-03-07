import os

input_folder = "tracks_svg"
output_folder = "tracks_png"

os.makedirs(output_folder, exist_ok=True)

for file in os.listdir(input_folder):
    if file.endswith(".svg"):
        
        svg_path = os.path.join(input_folder, file)
        png_path = os.path.join(output_folder, file.replace(".svg", ".png"))
        
        os.system(f'inkscape "{svg}" --export-type=png --export-width=1920 --export-height=1080 --export-filename="{png}"')
        
        print(f"Převedeno: {file}")
        
print("Hotovo!")