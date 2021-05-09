#!/usr/bin/env python

import bs4
import os
import sys
import requests
import argparse
import logging
import datetime
import shutil
import time
from dataclasses import dataclass

#-------------------------------#
#  Constants                    #
#-------------------------------#
BASE_URL_NS = "https://www.mangatown.com{rest}"
BASE_URL = "https://www.mangatown.com/{rest}"
URL = "https://www.mangatown.com/manga/{mangaName}"
LIST_CLASSNAME = "chapter_list"
IMAGE_ID = "image"
CHAPTER_FORMAT = "{serialNumber}__{title}"
FORBIDDEN_CHARS = ":"
SANITIZATION_MAPPING = {
        ":" : "_",
}


POLITENESS_FACTOR = 0.5     # delay between image downloads (seconds)

LOGGER_FILENAME = "mtowndl.log"
SUPPRESS_STDOUT = False                             # set to True for no printing at all
PROGBAR_LEN = 80
PROGBAR_ELEM = "▅"
#-------------------------------#
#  Data structures              #
#-------------------------------#
@dataclass
class Chapter:
    """Stores chapter names sand links"""
    index: int
    title: str
    url: str

#-------------------------------#
#  Helper functions             #
#-------------------------------#
def build_directory(args):
    if not os.path.exists(args.dirname):
        os.makedirs(args.dirname)
    os.chdir(args.dirname)

def build_chapter_directory(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    os.chdir(dirname)


def sanitize_chapter_title(title):
    for char in FORBIDDEN_CHARS:
        if char in title:
            title = title.replace(char, SANITIZATION_MAPPING[char])
    return title

def supply_schema(imgUrl):
    if "https" not in imgUrl[:6]:
        return "https:" + imgUrl
    return imgUrl

def print_cond_f(*args, **kwargs):
    if not SUPPRESS_STDOUT:
        print(*args, **kwargs)
#-------------------------------#
#  Primary functions            #
#-------------------------------#
def get_chapter_list(args):
    chapterList = []

    mangaHomeURL = URL.format_map(dict(mangaName=args.name))
    resp = requests.get(mangaHomeURL)

    if not resp.ok:
        return None
    
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    chapterContainer = soup.find("ul", {"class" : LIST_CLASSNAME})

    if not chapterContainer:
        print("Cont not found")

    chapters = chapterContainer.findAll("li")
    chapters.reverse()                      # in-place reversal

    for idx, chapter in enumerate(chapters):
        anchor = chapter.find("a")
        url = BASE_URL.format(rest=anchor["href"])
        title = sanitize_chapter_title(anchor.text.strip())

        chapterList.append( Chapter(idx, title, url) )

    return chapterList


def download_chapter(chapter):
    
    resp = requests.get(chapter.url)
    if resp.status_code != 200:
        logging.info("...Skipping chapter; bad response")
        return

    # get the number of pages from the navigation dropdown
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    navBar = soup.find("div", {"class": "page_select"})
    if not navBar:
        logging.info("...Skipping chapter; failed to locate page_select")
        return

    selectElem = navBar.find("select")
    if not selectElem:
        logging.info("...Skipping chapter; failed to get _select_ node")
        return
    
    options = selectElem.findAll("option")
    if not options:
        logging.info("...Skipping chapter; no pages at all")
        return

    pageLinks = [ x["value"] for x in options if 'featured' not in x.text.lower() ]

    
    # Create the directory and cd into it
    build_chapter_directory(chapter.title)


    # prepare the progressbar
    numPages = len(pageLinks)
    print_cond_f("[" + " "*(PROGBAR_LEN-2) + "]", end=" ")

    for idx, link in enumerate(pageLinks):


        link = BASE_URL_NS.format(rest=link)
        resp = requests.get(link)

        if resp.status_code != 200:
            logging.info(f"\t\t[Could not download page indexed {idx}")
            continue
        
        soup = bs4.BeautifulSoup(resp.text, "html.parser")
        imageLink = soup.find("img", {"id": IMAGE_ID})

        if not imageLink:
            logging.info(f"\t\t[Could not download page indexed {idx}")
            continue

        imageSrc = supply_schema(imageLink["src"])
        
        respImg = requests.get(imageSrc, stream=True)
        if respImg.status_code != 200:
            logging.info(f"\t\t[Could not download page indexed {idx}")
            continue
        
        # save to file
        imageFname = f"{idx+1}.png"
        with open(imageFname, "wb") as fi:
            respImg.raw_decode_content = True
            shutil.copyfileobj(respImg.raw, fi)


        progress = int((idx+1)/numPages * (PROGBAR_LEN-2))
        print_cond_f("\r[" + (PROGBAR_ELEM * progress) + (" " * (PROGBAR_LEN - 2 - progress)) + "]", end="")

        # Don't overwhelm the servers;
        time.sleep(POLITENESS_FACTOR)


        
    print_cond_f("\n")
    logging.info(f"...Finished Chapter")
    logging.info("-" * 64)
    
    os.chdir("..")

def main():
    logging.basicConfig(filename=LOGGER_FILENAME, encoding="utf-8", format='%(message)s', level=logging.INFO)
    logging.info(f"Started session at {datetime.datetime.now().strftime('%c')}\n\n")

    # TODO: decouple parsing from the main downloader
    # pass args to some function that will serve as actual main
    parser  = argparse.ArgumentParser()
    parser.add_argument("name", help="The manga's name, as it appears in the URL")
    parser.add_argument("dirname", help="Root folder for the manga. Chapters will be written to this directory")
    parser.add_argument("--cstart", help="Starting chapter, a, in [a,b] (closed interval of integers)")
    parser.add_argument("--cstop", help="Final chapter, b, in [a,b] (closed interval of integers)")


    args = parser.parse_args()

    # Validation
    assert(args.name is not None and args.dirname is not None)
    
    # set up the directory
    build_directory(args)


    # get the chapter list
    chapterList = get_chapter_list(args)
    if not chapterList:
        print("Could not download the chapter list. Terminating execution...")
        sys.exit()
    
    logging.info(f"Start downloading {args.name} at {datetime.datetime.now().strftime('%c')}")

    
    # prepare to download the specified chapters
    startIndex = 0
    stopIndex = len(chapterList) - 1

    if args.cstart and args.cstop:
        startIndex = int(args.cstart)-1
        stopIndex = int(args.cstop)-1


    for chapter in chapterList[startIndex:stopIndex+1]:
        print_cond_f(f"Downloading chapter {chapter.index+1}...")
        logging.info(f"Downloading chapter {chapter.index} => {chapter.title}")
        download_chapter(chapter)


    logging.info(f"\n\nSession ended at {datetime.datetime.now().strftime('%c')}\n\n")
    logging.info("="*32 + "\n")

if __name__ == '__main__':
    main()

