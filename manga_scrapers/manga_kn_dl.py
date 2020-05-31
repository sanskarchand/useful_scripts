#!/usr/bin/env python

# Sun 31 May 2020 09:45:22 PM +0545
# Updated downloader
# for mangakakalot and manganelo;
# They've added cloudflare protection, so the previous simple scrapes
# are useless;
# The lack of error-checking should not be a problem as this script is
# trivial to understand;

import argparse
from selenium import webdriver
import sys, os, time
from PIL import Image
import base64
from io import BytesIO

#-- BEGIN DEBUGTOOL --
DEBUG = True
def dprint(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs) 
#-- END DEBUGTOOL --

#-- BEGIN CONSTANTS --
TMP_DIREC = "tmp"
URL = "https://manga{0}.com/manga/{1}"
WAIT_TIME = 0.7                         # wait 700 msec between images
WAIT_CHAP = 5                           # wait 5 sec between chapters
ERROR_STRING = "ERR404"
CDN_DOMAINS = ['blogspot', 'mpcdn', 'mgimgcdn', 'mkklcdn']
DIV_NAMES = ["panel-story-chapter-list"]

# drawing script
# courtesy of mhmet mecek
# https://stackoverflow.com/questions/18424624/using-selenium-to-save-images-from-page
# save loaded image to canvas and use base64 codec-ing
SCRIPT_ = """
var dl_c = document.createElement('canvas');
var ctx = dl_c.getContext('2d');
var dl_img = document.getElementsByTagName('img')[0];
dl_c.height = dl_img.naturalHeight;
dl_c.width = dl_img.naturalWidth;
ctx.drawImage(dl_img, 0, 0, dl_img.naturalWidth, dl_img.naturalHeight);
var base64String = dl_c.toDataURL();
return base64String;
"""

#-- END CONSTANTS --

#-- BEGIN OBJECTS --
parser = argparse.ArgumentParser()
parser.add_argument("domain", help="Values: nelo or kaka")
parser.add_argument("mname", help="Name of manga in URL path")
parser.add_argument("fname", help="Name of folder to save chapters in")
parser.add_argument("--cstart", help="Chapter index to start with. Inclusive")
parser.add_argument("--cstop", help="Chapter index to stop at. Inclusive")
prog_args = parser.parse_args()

#another alternative method that didn't work
#fire_prof.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpeg, image/png, image/webp")

driver = webdriver.Firefox()
#-- END OBJECTS --


#-- BEGIN MAIN --
domain_name = "nelo" if prog_args.domain == "nelo" else "kakalot"
full_url = URL.format(domain_name, prog_args.mname)

print("...Downloading webpage...")
driver.get(full_url)

if "404" in driver.title:
    print(ERROR_STRING)
    driver.quit()
    sys.exit()


# get the chaptes in chronological order
chapters_list = driver.find_elements_by_class_name("chapter-name")
chapters_list.reverse()
chapter_names = [web_elem.text for web_elem in chapters_list]
chapter_urls = [web_elem.get_attribute("href") for web_elem in chapters_list]

# preprocess chapter names
chapter_names = [name.replace(":", "__") for name in chapter_names]

start_chap = None
stop_chap = None

# Interactive mode - start and stop args have not been supplied
if not prog_args.cstart:
    print("Chapters: ")

    for idx, chap_name in enumerate(chapter_names):
        print("{0}\t:{1}".format(idx, chap_name))

    start_chap = input("Start Index: ")
    stop_chap = input("Stop Index: ")
else:
    start_chap = prog_args.cstart
    stop_chap = prog_args.cstop

# Parse indices
start_chap = int(start_chap)
stop_chap = int(stop_chap)

fname = prog_args.fname
# Make the folder
if not os.path.exists(fname):
    os.mkdir(fname)

for chap_index in range(start_chap, stop_chap+1):
    
    print("Downloading Chapter indexed {0}...".format(chap_index))
    
    url = chapter_urls[chap_index]
    chapter_name = chapter_names[chap_index]

    # create path
    chapter_path = os.path.join(fname, chapter_name)
    if not os.path.exists(chapter_path):
        os.makedirs(chapter_path)
    
    driver.get(url)

    if "404" in driver.title:
        print(ERROR_STRING)
        driver.quit()
        sys.exit()


    # Then, get image links
    image_elems = driver.find_elements_by_tag_name('img')

    # Check for correct domain
    final_elems= []
    for elem in image_elems:
        source = elem.get_attribute("src")
        conditionals = [domain_str in source for domain_str in CDN_DOMAINS]
        if any(conditionals):
            final_elems.append(elem)
   


    urls = [elem.get_attribute("src") for elem in final_elems]

    i = 1
    for url in urls:
        dprint("Downloading ", url)
        driver.get(url) # should autosav
        
        img_base64_dat = driver.execute_script(SCRIPT_)
        ind = img_base64_dat.find(",")
        img_base64_dat = img_base64_dat[ind:]
        im = Image.open(BytesIO(base64.b64decode(img_base64_dat)))
        im = im.convert("RGB")
        im.save(os.path.join(chapter_path, str(i) + ".jpg"), "JPEG")

        time.sleep(WAIT_TIME)
        i += 1


    time.sleep(WAIT_CHAP)

#-- END MAIN --
