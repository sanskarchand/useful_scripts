#!/usr/bin/env python
import time
import os
from PIL import Image, ImageFont, ImageDraw
import signal
import sys

#path from home
PATH = 'Pictures/screensaver_img/mylockscreen.png'
FILLCOL = '#087C83'
FONT_SIZE = 50
FONT = ImageFont.truetype('/home/<USERNAME>/Downloads/fonts/ttf-envy-code-r/src/Envy Code R PR7/Envy Code R Bold.ttf', FONT_SIZE)

home_path = os.path.expanduser('~')
orig_file_path = os.path.join(home_path, PATH)
image = Image.open(orig_file_path)
rind = orig_file_path.rfind('.')
alt_path = orig_file_path[:rind] + "_1_" + orig_file_path[rind:]

file_path = orig_file_path

def sigterm_handler(_signo, _stack_frame):
    # restore the original file
    if os.path.exists(alt_path):
        os.rename(alt_path, orig_file_path)
    sys.exit(0)

#register signal handler
signal.signal(signal.SIGTERM, sigterm_handler)

def create_image_timestamp(src_img):
    global file_path

    w, h = src_img.size

    ts_string = time.strftime('%H:%M %a')

    ts_width = int(0.2 * w)
    ts_height = int(0.2 * h)

    new_img = Image.new('RGB', (ts_width, ts_height), FILLCOL)

    time_draw = ImageDraw.Draw(new_img)
    time_draw.text((10, 10), ts_string, font=FONT)

    src_img.paste(new_img, (int(0.8*w), int(0.8*h)))
    

    # remove old file
    os.remove(file_path)

    if file_path == orig_file_path:
        file_path = alt_path
    else:
        file_path = orig_file_path

    src_img.save(file_path, "PNG")



def main():
    
    #save a backup of the original
    image.save("lockscreen_img_backup.png", "PNG")

    while True:
        create_image_timestamp(image)
        time.sleep(60)
main()
