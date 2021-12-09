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
import datetime
import sys

#-- BEGIN DEBUGTOOL --
DEBUG = True
def dprint(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs) 
#-- END DEBUGTOOL --

#-- BEGIN CONSTANTS --
METADATA = True
TMP_DIREC = "tmp"
URL = "https://manga{0}.com/manga/{1}"
URL_ALT = "https://manga{0}.com/{1}"    # for manga named read-{hash}
URL_ALT2 = "https://{0}.com/{1}"        # for readmanganato
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"

WAIT_TIME = 0.7                         # wait 700 msec between images
WAIT_CHAP = 5                           # wait 5 sec between chapters
ERROR_STRING = "ERR404"
CDN_DOMAINS = ['blogspot', 'mpcdn', 'mgimgcdn', 'mkklcdn']
FILTER_DOMAIN_STRINGS = ['avt.']         # probably downloads avatars; ignore these images
DIV_NAMES = ["panel-story-chapter-list"]

#-- END CONSTANTS --

#-- BEGIN OBJECTS --
parser = argparse.ArgumentParser(epilog="Example usage:  python manga_kn_dl.py kakalot swot Swot_Manga")
parser.add_argument("domain", help="Values: nelo, kaka, nato")
parser.add_argument("mname", help="Name of manga in URL path")
parser.add_argument("fname", help="Name of folder to save chapters in")
parser.add_argument("--cstart", help="Chapter index to start with. Inclusive")
parser.add_argument("--cstop", help="Chapter index to stop at. Inclusive")
parser.add_argument('--clist', help='Comma-separated chapter list', type=str)
prog_args = parser.parse_args()

#another alternative method that didn't work
#fire_prof.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpeg, image/png, image/webp")

profile = webdriver.FirefoxProfile()
profile.set_preference("general.useragent.override", USER_AGENT)
driver = webdriver.Firefox(profile)
#-- END OBJECTS --


#-- BEGIN MAIN --
domain_name = prog_args.domain   #"nelo" if prog_args.domain == "nelo" else "kakalot"

fmtURL  = None
if 'read-' in prog_args.mname:
    fmtURL = URL_ALT
else:
    fmtURL = URL

full_url = fmtURL.format(domain_name, prog_args.mname)
if domain_name == "nato":
    full_url = URL_ALT2.format("readmanganato", prog_args.mname)

print("...Downloading webpage...", full_url)
driver.get(full_url)

if "404" in driver.title:
    print(ERROR_STRING)
    driver.quit()
    sys.exit()


def getChapterLinks():

    # method 1:
    anchor_elems = driver.find_elements_by_css_selector(".chapter-name")
    if anchor_elems:
        return anchor_elems
    
    # method 2:
    chapters_list = driver.find_elements_by_css_selector(".panel-story-chapter-list .a-h")
    #chapters_list.reverse()
    anchor_elems = [web_elem.find_elements_by_css_selector("span > a")[0] for web_elem in chapters_list]
    if anchor_elems:
        return anchor_elems

    # method 3:
    chapters_list = driver.find_elements_by_css_selector(".chapter-list .row")
    #chapters_list.reverse()
    anchor_elems = [web_elem.find_elements_by_css_selector("span > a")[0] for web_elem in chapters_list]
    if anchor_elems:
        return anchor_elems


anchor_elems = getChapterLinks()

chapter_names = [elem.text for elem in anchor_elems]
chapter_urls = [elem.get_attribute("href") for elem in anchor_elems]

# preprocess chapter names
chapter_names = [name.replace(":", "__") for name in chapter_names]


chapter_names.reverse()
chapter_urls.reverse()

chap_index_list = None

# Interactive mode - start and stop args have not been supplied
if not (prog_args.cstart or prog_args.clist):
    print("Chapters: ")

    for idx, chap_name in enumerate(chapter_names):
        print("{0}\t:{1}".format(idx, chap_name))

    start_chap = input("Start Index: ")
    stop_chap = input("Stop Index: ")
    start_chap = int(start_chap)
    stop_chap = int(stop_chap)
    chap_index_list = range(start_chap, stop_chap+1)
elif prog_args.clist:
    chap_index_list = [int(chap_index) for chap_index in prog_args.clist.split(',')]
elif prog_args.cstart:
    start_chap = prog_args.cstart
    stop_chap = prog_args.cstop
    start_chap = int(start_chap)
    stop_chap = int(stop_chap)
    chap_index_list = range(start_chap, stop_chap+1)
else:
    print("Chapters not provided")
    driver.quit()
    sys.exit()

    
# Parse indices


fname = prog_args.fname
# Make the folder
if not os.path.exists(fname):
    os.mkdir(fname)

for chap_index in chap_index_list:
    
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
        filters = [domain_str in source for domain_str in FILTER_DOMAIN_STRINGS]
        if any(conditionals) and not any(filters):
            final_elems.append(elem)
    
    for idx, image_elem in enumerate(final_elems):
        path = os.path.join(chapter_path, f"{idx+1}.png")
        scrn = image_elem.screenshot_as_png
        with open(path, "wb") as f:
            f.write(scrn)

        time.sleep(WAIT_TIME)
    time.sleep(WAIT_CHAP)

driver.close()

if METADATA:
    with open(os.path.join(fname, "info.txt"), "w") as f:
        stri = f"Downloaded on {datetime.datetime.now().strftime('%c')} using manga_kn_dl.py"
        f.write(stri)

#-- END MAIN --
