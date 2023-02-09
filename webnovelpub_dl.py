#!/usr/bin/env python

import requests
import bs4
import argparse
import sys
from dataclasses import dataclass
import pdfkit
import os
import time
import subprocess
import datetime
#--------   constants   --------
URL_BASE = "https://www.webnovelpub.com{rest}"
URL_MAIN = "https://www.webnovelpub.com/novel/{slug}/chapters/page-{page_num}"
POLITENESS_FACTOR = 0.2                         # delay between downloads, in seconds
#--------   /constants  --------
headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/109.0."
}
    


@dataclass
class Chapter:
    """Class for storing chapters and links"""
    index: int
    name: str
    url: str


def clean_chapter_anme(chapName):
    """
    Replace colons and other troublesome characters
    """
    return chapName.replace(':', '_')

def get_chapter_content(chapter_html):
    soup = bs4.BeautifulSoup(chapter_html, 'html.parser')
    div = soup.find("div", {"id": "chapter-container"})
    content = div.find_all("p")

    return content

def make_pdf(chapter_list, slug):

    #generate default toc
    if not os.path.exists("default_toc.xsl"):
        with open('default_toc.xsl', 'w') as outfile:
            subprocess.call(['wkhtmltopdf', '--dump-default-toc-xsl'], stdout=outfile)

    toc = {
        'xsl-style-sheet': 'default_toc.xsl'
    }

    body = ''
    for index in range(len(chapter_list)):
        print(f"Processing chapter {index+1}...")
        chapter = chapter_list[index]
        resp = requests.get(URL_BASE.format(rest=chapter.url), headers=headers)
        content = [str(c)  for c in get_chapter_content(resp.text)]

        # add this chapter to the body
        if index == 0:
            body += f'<h2>{chapter.name}</h2>'+ "".join(content)
        else:
            body += f'<h2 style="page-break-before: always;">{chapter.name}</h2>'+ "".join(content)

        time.sleep(POLITENESS_FACTOR)

    options = {
            'margin-bottom': '20mm',
            'footer-center': '[page]'
    }
        
    output = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
            </head>
            <body>
            {body}
                <p style="page-break-before: always;">
                    <b>Extra metadata</b>
                    <p>Downloaded from: webnovelpub</p>
                    <p >Created on: {date} </p>
                    <p>Created using: <a href="https://github.com/sanskarchand/useful_scripts">webnovel</a></p>
                </p>
            </body>
            </html>""".format(body=body, 
                            date=str(datetime.datetime.now()),
                    )      # handle unicode

    #pdfkit.from_string(output, "{name}.pdf", options=options)
    
    pdfkit.from_string(output, f"{slug}.pdf", toc=toc, options=options)

def extract_chapters(html_page, slug=None):
    chapter_list = []

    soup = bs4.BeautifulSoup(html_page, 'html.parser')
    numPagesCont = soup.find("li", {"class": "PagedList-skipToLast"})
    lastPageURL =  numPagesCont.find("a")["href"] 

    ind = lastPageURL.rfind("-")
    totalNumPages = int(lastPageURL[ind+1:])
    headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/109.0."
    }
    

        
    for page_num in  range(1, totalNumPages):
        
        if page_num != 1: 
            r = requests.get(URL_MAIN.format(slug=slug, page_num=page_num), headers=headers)
            if r.status_code != 200:
                print(f"Error: Could not get main page (Status {r.status_code}). Aborting...")
                sys.exit(1)

            soup = bs4.BeautifulSoup(r.text, 'html.parser')

        chapterListCurrent = soup.find_all("li", attrs={"data-chapterno": True})
        chapterAnchors = [chap.find('a') for chap in chapterListCurrent]
        for idx, chap in enumerate(chapterAnchors):
            chapterName = chap["title"]
            chapterURL = chap['href']
            chapter_list.append( Chapter(idx, chapterName, chapterURL) )

        time.sleep(POLITENESS_FACTOR)

    return chapter_list

def main():
    if len(sys.argv) == 1:
        slug = "the-regressed-demon-lord-is-kind-04022146"
    else:
        slug = sys.argv[1]
    
    headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/109.0."
    }
    
    
    print("Getting chapter list...")
    r = requests.get(URL_MAIN.format(slug=slug, page_num=1), headers=headers)
    if r.status_code != 200:
        print(f"Error: Could not get main page (Status {r.status_code})")
    
    chapter_list = extract_chapters(r.text, slug)
    print(f"There are {len(chapter_list)} chapters")
    make_pdf(chapter_list, slug)

if __name__ == '__main__':
    main()
