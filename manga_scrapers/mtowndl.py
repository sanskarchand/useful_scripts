#!/usr/bin/env python

import bs4
import os
import sys
import requests
import argparse
from dataclasses import dataclass

#-------------------------------#
#  Constants                    #
#-------------------------------#
BASE_URL = "https://www.mangatown.com/{rest}"
URL = "https://www.mangatown.com/manga/{mangaName}"
LIST_CLASSNAME = "chapter_list"
CHAPTER_FORMAT = "{serialNumber}__{title}"
FORBIDDEN_CHARS = ":"
SANITIZATION_MAPPING = {
        ":" : "_",
}


POLITENESS_FACTOR = 0.5     # delay between image downloads (seconds)

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


def sanitize_chapter_title(title):
    for char in FORBIDDEN_CHARS:
        if char in title:
            title = title.replace(char, SANITIZATION_MAPPING[char])
    return title

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
    


def main():
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


    for chapter in chapterList:
        print(chapter)

    #TODO:  continue this...  (ौा笑)
    

if __name__ == '__main__':
    main()
