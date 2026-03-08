import os
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

input_folder = "tracks_svg"
output_folder = "tracks_png"

os.makedirs(output_folder, exist_ok=True)

for file in os.listdir(input_folder):

    if file.endswith(".svg"):

        svg_path = os.path.join(input_folder, file)
        png_path = os.path.join(output_folder, file.replace(".svg", ".png"))

        drawing = svg2rlg(svg_path)
        renderPM.drawToFile(drawing, png_path, fmt="PNG")

        print("Converted:", file)

print("Hotovo!")