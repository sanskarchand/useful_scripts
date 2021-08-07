#!/usr/bin/env python

import requests
import bs4
import argparse
import sys
from dataclasses import dataclass
#import cloudscraper
import pdfkit
import os
import time
import subprocess
import datetime
#--------   constants   --------
URL_MAIN = "https://novelfull.com/{novelName}"
URL_CHAPTER  = "https://novelfull.com{chapterLink}"
URL = "https://novelfull.com/{novelName}.html?page={pageNum}"
POLITENESS_FACTOR = 1                         # delay between downloads, in seconds

# html5lib is needed because the HTML of novelfull is often broken
HTML_PARSER = "html5lib"                        # alt: html.parser

HEADERS_TO_REPLACE = ["h3", "h4"]
#--------   /constants  --------


@dataclass
class Chapter:
    """Class for storing chapters and links"""
    index: int
    name: str
    url: str                        # useless for this case (or change format of URL_CHAPTER)


def clean_chapter_name(chapName):
    """
    Replace colons and other troublesome characters
    """
    return chapName.replace(':', '_')


def get_chapter_content(chapter_html):
    soup = bs4.BeautifulSoup(chapter_html, HTML_PARSER)
    div = soup.find("div", {"id": "chapter-content"})
    node = div.find("script")
    content = []
    while True:
        node = node.nextSibling
        if node.name == 'a':
            break
        content.append(node)

    return content


def download_from_url(url):
    resp = requests.get(url)
    if not resp.ok:
        return None
    
    return resp.text


def get_chapter_processed(chapter_list, chapter_idx):
        
        ch1 = chapter_list[chapter_idx]
        contents = download_from_url(URL_CHAPTER.format(chapterLink=ch1.url))
        soup = bs4.BeautifulSoup(contents, HTML_PARSER)

        content = soup.find("div", {"id": "chapter-content"})

        # replace h3 headings with h2 headers
        # for proper chapter titles 
        for header in HEADERS_TO_REPLACE:
            hx = content.find(header)
            if hx:
                h2 = soup.new_tag("h2")
                h2.string = hx.string
                hx.replace_with(h2)
        

        ''' 
        adjacentTags = soup.findAll("ins")
        for tag in adjacentTags:
            if 'data-ad-slot' in tag.attrs:
                div = tag.findNext('div')
                p = tag.findNext('p')
                if p:
                    contentString += str(p)
                if div:
                    contentString += str(p)
        '''
        
        for div in content.findAll("div", {"class": "ads"}):
            div.decompose()

        for script in content.findAll("script"):
            script.decompose()
        
        return str(content) #+ contentString

def make_pdf(chapter_list, novelName):

    #generate default toc
    if not os.path.exists("default_toc.xsl"):
        with open('default_toc.xsl', 'w') as outfile:
            subprocess.call(['wkhtmltopdf', '--dump-default-toc-xsl'], stdout=outfile)

    toc = {
        'xsl-style-sheet': 'default_toc.xsl'
    }

    body = ''
    print("Downloading chapters and generating the PDF file...")

    #for index in range(len(chapter_list)):
    num_processed = 0
    print(f"Downloading  {len(chapter_list)} chapters")
    for index in range(len(chapter_list)):
        num_processed += 1
        if num_processed % 50 == 0:
            print(f"Processed {num_processed} chapters")

        chapter = chapter_list[index]
        content = get_chapter_processed(chapter_list, index)

        # add this chapter to the body
        if index == 0:
            #body += f'<h2>{chapter.name}</h2>'+ content
            body += content
        else:
            #body += f'<h2 style="page-break-before: always;">{chapter.name}</h2>'+ "".join(content)
            body += '<hr style="page-break-before: always;"/>' + content

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
                    <p>Created using: novelfull_dl.py /p>
                </p>
            </body>
            </html>""".format(body=body, 
                            date=str(datetime.datetime.now()),
                            name=novelName,
                            url=URL_MAIN.format(novelName=novelName)
                    )      # handle unicode

    #pdfkit.from_string(output, "{name}.pdf", options=options)
    
    pdfkit.from_string(output, f"{novelName}.pdf", toc=toc, options=options)

def extract_chapters(novelName, html_page):
    
    print("Obtaining initial data...")

    def extract_links_and_titles(pageSoup):
        title_list_cont = pageSoup.find("div", {"id": "list-chapter"})

        # should be two containers
        chap_containers = title_list_cont.findAll("ul", {"class": "list-chapter"})
        li = []
        for cont in chap_containers:
            li.extend([(anchor["title"], anchor["href"]) for anchor in cont.select("li > a")])
        return li

    chapter_list = []
    soup = bs4.BeautifulSoup(html_page, HTML_PARSER)

    title_list_cont = soup.find("div", {"id": "list-chapter"})

    pagination = title_list_cont.find("ul", {"class": "pagination"})
    last = pagination.find("li", {"class": "last"})
    last_page = int( (last.select("li > a")[0]["data-page"]).strip() ) + 1

    #title_list = soup.find("ul", {"class": "list-chapter"})

    title_link_list = []
    title_link_list.extend(extract_links_and_titles(soup)) # for page 1
    
    print("Gathering links...")

    for pageNum in range(2, last_page+1):
        time.sleep(POLITENESS_FACTOR)

        page_content = download_from_url(URL.format(novelName=novelName, pageNum=pageNum))
        page_soup = bs4.BeautifulSoup(page_content, HTML_PARSER)
        title_link_list.extend(extract_links_and_titles(page_soup))
    
    for idx, (title, link) in enumerate(title_link_list):
        chapter_list.append( Chapter(idx, title, link) )

    #chapter_list.append( Chapter(idx, chapterName, chapterURL) )

    return chapter_list

def main():
    if len(sys.argv) == 1:
        novelName = 'my-senior-brother-is-too-steady'
    else:
        novelName = sys.argv[1]

    

    page_content = download_from_url(URL.format(novelName=novelName, pageNum=1))
    
    chapter_list = extract_chapters(novelName, page_content)
    #print(chapter_list)
    make_pdf(chapter_list, novelName)

if __name__ == '__main__':
    main()
