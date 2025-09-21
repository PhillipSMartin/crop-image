import os
import sys
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time

def get_union_bbox(driver, margin=20):
    # Get bounding boxes of all visible elements except those with class 'bridge-diagram'
    rects = driver.execute_script('''
        var rects = [];
        function isVisible(elem) {
            var style = window.getComputedStyle(elem);
            return style.display !== 'none' && style.visibility !== 'hidden' && elem.offsetWidth > 0 && elem.offsetHeight > 0;
        }
        var all = document.body.getElementsByTagName('*');
        for (var i = 0; i < all.length; i++) {
            var elem = all[i];
            if (isVisible(elem) && !(elem.classList && elem.classList.contains('bridge-diagram'))) {
                var r = elem.getBoundingClientRect();
                rects.push({left: r.left, top: r.top, right: r.right, bottom: r.bottom});
            }
        }
        return rects;
    ''')
    if not rects:
        # fallback to body
        rect = driver.execute_script('''
            var r = document.body.getBoundingClientRect();
            return {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
        ''')
        rects = [rect]
    left = min(r['left'] for r in rects)
    top = min(r['top'] for r in rects)
    right = max(r['right'] for r in rects)
    bottom = max(r['bottom'] for r in rects)
    # Add margin
    left = max(int(left) - margin, 0)
    top = max(int(top) - margin, 0)
    right = int(right) + margin
    bottom = int(bottom) + margin
    return left, top, right, bottom

def render_and_crop_html_selenium(html_path, output_img_path, margin=20):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)

    abs_html_path = os.path.abspath(html_path)
    driver.get('file://' + abs_html_path)
    time.sleep(1)

    screenshot_path = 'selenium_rendered.png'
    driver.save_screenshot(screenshot_path)

    left, top, right, bottom = get_union_bbox(driver, margin)
    driver.quit()

    with Image.open(screenshot_path) as img:
        cropped = img.crop((left, top, right, bottom))
        if cropped.mode in ("RGBA", "LA"):
            background = Image.new("RGB", cropped.size, (255, 255, 255))
            background.paste(cropped, mask=cropped.split()[-1])
            background.save(output_img_path)
        else:
            cropped.save(output_img_path)
    os.remove(screenshot_path)

def process_directory_selenium(directory, margin=20, force=False):
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            html_path = os.path.join(directory, filename)
            output_img_path = os.path.join(directory, filename[:-5] + '.png')
            if not force and os.path.exists(output_img_path):
                print(f"Skipping {html_path} (output exists)")
                continue
            print(f"Processing {html_path} -> {output_img_path}")
            render_and_crop_html_selenium(html_path, output_img_path, margin)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch render and crop HTML files in a directory using Selenium.")
    parser.add_argument("directory", help="Directory containing .html files")
    parser.add_argument("-m", "--margin", type=int, default=20, help="Margin in pixels around detected content")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite of existing .png files")
    args = parser.parse_args()

    directory = args.directory
    margin = args.margin
    force = args.force
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory.")
        sys.exit(1)
    process_directory_selenium(directory, margin, force)
