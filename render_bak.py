
from html2image import Html2Image
from PIL import Image
import os
import sys

import argparse

def render_and_crop_html(html_path, output_img_path, new_width=184, new_height=346, left_crop=None):
    hti = Html2Image()
    hti.screenshot(
        html_file=html_path,
        save_as='rendered.png',
        size=(800, 600)
    )
    with Image.open('rendered.png') as img:
        width, height = img.size
        if left_crop is not None:
            left = max(left_crop, 0)
            right = left + new_width
        else:
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
    if argc >= 4:
        try:
            new_height = int(argv[3])
        except ValueError:
            print("Height must be an integer.")
            sys.exit(1)
    else:
        new_height = 346
    if argc == 5:
        try:
            left_crop = int(argv[4])
        except ValueError:
            print("Left crop must be an integer.")
            sys.exit(1)
    else:
        left_crop = None
    return new_width, new_height, left_crop

def process_directory(directory, new_width=184, new_height=346, left_crop=None, force=False):
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            html_path = os.path.join(directory, filename)
            output_img_path = os.path.join(directory, filename[:-5] + '.png')
            if not force and os.path.exists(output_img_path):
                print(f"Skipping {html_path} (output exists)")
                continue
            print(f"Processing {html_path} -> {output_img_path}")
            render_and_crop_html(html_path, output_img_path, new_width, new_height, left_crop)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render and crop HTML files in a directory.")
    parser.add_argument("directory", help="Directory containing .html files")
    parser.add_argument("width", nargs="?", type=int, default=184, help="Width of crop")
    parser.add_argument("height", nargs="?", type=int, default=346, help="Height of crop")
    parser.add_argument("left_crop", nargs="?", type=int, help="Crop this many pixels from the left (optional)")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite of existing .png files")
    args = parser.parse_args()

    directory = args.directory
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory.")
        sys.exit(1)
    new_width = args.width
    new_height = args.height
    left_crop = args.left_crop
    force = args.force
    process_directory(directory, new_width, new_height, left_crop, force)
