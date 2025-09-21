import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time

def get_visible_bbox(driver, margin=20):
    # Get bounding box of the body element
    rect = driver.execute_script('''
        var elem = document.body;
        var rect = elem.getBoundingClientRect();
        return {left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom, width: rect.width, height: rect.height};
    ''')
    # Add margin
    left = max(int(rect['left']) - margin, 0)
    top = max(int(rect['top']) - margin, 0)
    right = int(rect['right']) + margin
    bottom = int(rect['bottom']) + margin
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
    time.sleep(1)  # Wait for rendering

    # Take full page screenshot
    screenshot_path = 'selenium_rendered.png'
    driver.save_screenshot(screenshot_path)

    left, top, right, bottom = get_visible_bbox(driver, margin)
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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python render_selenium.py <html_path> <output_img_path> [margin]")
        sys.exit(1)
    html_path = sys.argv[1]
    output_img_path = sys.argv[2]
    margin = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    render_and_crop_html_selenium(html_path, output_img_path, margin)
