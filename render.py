
from html2image import Html2Image
from PIL import Image
import os
import sys

def render_and_crop_html(html_path, output_img_path, new_width=184, new_height=346):
    hti = Html2Image()
    hti.screenshot(
        html_file=html_path,
        save_as='rendered.png',
        size=(800, 600)
    )
    with Image.open('rendered.png') as img:
        width, height = img.size
        left = max((width - new_width) // 2, 0)
        right = left + new_width
        top = 0
        bottom = min(new_height, height)
        cropped = img.crop((left, top, right, bottom))
        if cropped.mode in ("RGBA", "LA"):
            background = Image.new("RGB", cropped.size, (255, 255, 255))
            background.paste(cropped, mask=cropped.split()[-1])
            background.save(output_img_path)
        else:
            cropped.save(output_img_path)
    os.remove('rendered.png')

def parse_args(argc, argv):
    if argc >= 3:
        try:
            new_width = int(argv[2])
        except ValueError:
            print("Width must be an integer.")
            sys.exit(1)
    else:
        new_width = 184
    if argc == 4:
        try:
            new_height = int(argv[3])
        except ValueError:
            print("Height must be an integer.")
            sys.exit(1)
    else:
        new_height = 346
    return new_width, new_height

def process_directory(directory, new_width=184, new_height=346):
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            html_path = os.path.join(directory, filename)
            output_img_path = os.path.join(directory, filename[:-5] + '.png')
            print(f"Processing {html_path} -> {output_img_path}")
            render_and_crop_html(html_path, output_img_path, new_width, new_height)

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc < 2 or argc > 4:
        print("Usage: python render.py <directory> [width] [height]")
        sys.exit(1)
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory.")
        sys.exit(1)
    new_width, new_height = parse_args(argc, sys.argv)
    process_directory(directory, new_width, new_height)
