#!/usr/bin/env python

import requests
import bs4
import argparse
import sys
from dataclasses import dataclass
import cloudscraper
import pdfkit
import os
import time
import subprocess
import datetime
#--------   constants   --------
URL_CHAPTER = "https://www.wuxiaworld.com{chapPath}"
URL = "https://www.wuxiaworld.com/novel/{novelName}"
POLITENESS_FACTOR = 0.2                         # delay between downloads, in seconds
#--------   /constants  --------


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
    div = soup.find("div", {"id": "chapter-content"})
    node = div.find("script")
    content = []
    while True:
        node = node.nextSibling
        if node.name == 'a':
            break
        content.append(node)

    return content

def make_pdf(chapter_list, name, scraper):

    #generate default toc
    if not os.path.exists("default_toc.xsl"):
        with open('default_toc.xsl', 'w') as outfile:
            subprocess.call(['wkhtmltopdf', '--dump-default-toc-xsl'], stdout=outfile)

    toc = {
        'xsl-style-sheet': 'toc.xsl'
    }

    body = ''
    for index in range(len(chapter_list)):
        print(f"Processing chapter {index+1}...")
        chapter = chapter_list[index]
        resp = scraper.get(URL_CHAPTER.format(chapPath=chapter.url))
        content = [str(c) for c in get_chapter_content(resp.text)]

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
                    <p>Downloaded from: <a href="{url}">{name}</a></p>
                    <p >Created on: {date} </p>
                    <p>Created using: <a href="https://github.com/sanskarchand/useful_scripts">wuxial-dl</a></p>
                </p>
            </body>
            </html>""".format(body=body, 
                            date=str(datetime.datetime.now()),
                            name=name,
                            url=URL.format(novelName=name)
                    )      # handle unicode

    #pdfkit.from_string(output, "{name}.pdf", options=options)
    
    pdfkit.from_string(output, f"{name}.pdf", toc=toc, options=options)

def extract_chapters(html_page):
    chapter_list = []

    soup = bs4.BeautifulSoup(html_page, 'html.parser')
    chapterLists = soup.find_all("li", attrs={"class": "chapter-item"})
    chapterAnchors = [chap.find('a') for chap in chapterLists]
    for idx, chap in enumerate(chapterAnchors):
        chapterName = chap.text.replace('\n', '')
        chapterURL = chap['href']
        
        chapter_list.append( Chapter(idx, chapterName, chapterURL) )

    return chapter_list

def main():
    if len(sys.argv) == 1:
        novelName = 'the-second-coming-of-gluttony'
    else:
        novelName = sys.argv[1]

    
    scraper = cloudscraper.create_scraper()

    r = scraper.get(URL.format(novelName=novelName))
    if r.status_code != 200:
        print(f"Error: Could not get main page (Status {r.status_code})")
    
    chapter_list = extract_chapters(r.text)
    make_pdf(chapter_list, novelName, scraper)

if __name__ == '__main__':
    main()
