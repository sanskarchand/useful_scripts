#!/usr/bin/env python
import time
import os
from PIL import Image, ImageFont, ImageDraw
import signal
import sys
import subprocess
#import psutil

# Meant to be used with xflock4 and xfce4-screensaver
# only arg is PID of xflock4
#path from home
FNAME_A = 'Pictures/screensaver_img/lockA.png'
FNAME_B = 'Pictures/screensaver_img/lockB.png'
ERRFILE = 'sans_scrnlock_outerr.txt'
FILLCOL = '#087C83'
FONT_SIZE = 64
FONT = ImageFont.truetype('/home/drakinosh/Downloads/fonts/ttf-envy-code-r/src/Envy Code R PR7/Envy Code R Bold.ttf', FONT_SIZE)

home_path = os.path.expanduser('~')
if os.path.exists(os.path.join(home_path, FNAME_A)):
    orig_file_path = os.path.join(home_path, FNAME_A)
    alt_path = os.path.join(home_path, FNAME_B)
else:
    orig_file_path = os.path.join(home_path, FNAME_B)
    alt_path = os.path.join(home_path, FNAME_A)

file_path = orig_file_path
error_path = os.path.join(home_path, ERRFILE)
'''
sys.stdout = open(error_path, 'w')
sys.stderr = sys.stdout
'''


def should_exit():
    ret = subprocess.check_output(["xfce4-screensaver-command", "-t"])
    return "0 seconds" in str(ret)

def cleanup():
    if os.path.exists(alt_path):
        os.rename(alt_path, orig_file_path)
    sys.exit(0)

def sig_handler(_signo, _stack_frame):
    cleanup()

#register signal handlers
signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT, sig_handler)

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
    
    
    del_file = file_path

    if file_path == orig_file_path:
        file_path = alt_path
    else:
        file_path = orig_file_path

    src_img.save(file_path, "PNG")
    time.sleep(10)               #10 secs for xfce4-screensaver to transition
    os.remove(del_file)     



def main():
    #save a backup of the original
    bkup_path = os.path.join(os.path.expanduser('~'), "lockscreen_img_backup.png")
    image = Image.open(orig_file_path)
    image.save(bkup_path, "PNG")
    
    while True:
        create_image_timestamp(image)
        
        if should_exit():
            cleanup()


        time.sleep(50)
main()
