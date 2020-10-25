#!/usr/bin/env python

import argparse
import json
import os, shutil, sys
import requests
import itertools, operator

BASE_URL = 'https://mangadex.org/api/{}'
BASE_URL_MANGA = BASE_URL.format('manga/{}')
BASE_URL_CHAPTER = BASE_URL.format('chapter/{}')

ALLOWED_LANGS = ('English',)
CHAP_ID_FORMAT = 'Vol_{}_Ch_{}__'
DISALLOWED_CHARS = " :?'!"
REPLACEMENT_CHAR = "_"

LANG_MAP = {'English': 'ENG'}
def map_language(lang):
    if lang in LANG_MAP.keys():
        return LANG_MAP[lang]
    return lang

def filter_title(title):
    new_title = ''.join(char if char not in DISALLOWED_CHARS else REPLACEMENT_CHAR for char in title)
    return new_title

def download_chapter(lang, chapter_id):
    lang = map_language(lang)
    url_chapter = BASE_URL_CHAPTER.format(chapter_id)

    resp_chapter = requests.get(url_chapter)
    chapter_data = None
    if resp_chapter.status_code == 200:
        chapter_data = json.loads(resp_chapter.text)
    else:
        print('Failure. Status code: ', resp_chapter.status_code)
        print('Skipping chapter...')
        return
    
    vol_num = chapter_data['volume']
    chap_num = chapter_data['chapter']
    title = chapter_data['title']

    hash_ = chapter_data['hash']
    server_ = chapter_data['server']

    # make directory
    clean_title = filter_title(title)
    serial_id = CHAP_ID_FORMAT.format(vol_num, chap_num)
    dirname = '[{}]'.format(lang) + serial_id + clean_title
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    os.chdir(dirname)
    
    print("Downloading to ", dirname)
    page_no = 0
    for page_fname in chapter_data['page_array']:
        page_no += 1
        url = server_ + hash_ + '/' + page_fname
        ind = page_fname.rindex('.')
        extension = page_fname[ind:]
        fname = str(page_no) + extension

        resp = requests.get(url, stream=True)
        if resp.status_code == 200:
            with open(fname, 'wb') as f:
                resp.raw.decode_content = True
                shutil.copyfileobj(resp.raw, f)

    os.chdir('..')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="manga ID, as see in title URL")
    parser.add_argument("dirname", help="directory name to save manga to")
    parser.add_argument("--cstart", help="serial number of starting chapter (count from one)")
    parser.add_argument("--cstop", help="serial number of last chapter")

    my_args = parser.parse_args()

    #Get data
    assert(my_args.id is not None and my_args.dirname is not None)
    manga_id = my_args.id
    manga_dirname = my_args.dirname
    
    # make main directory
    if not os.path.exists(manga_dirname):
        os.makedirs(manga_dirname)
    os.chdir(manga_dirname)

    url_manga_mdata = BASE_URL_MANGA.format(manga_id)
    resp_manga = requests.get(url_manga_mdata)
    manga_metadata = None
    if resp_manga.status_code == 200:
        manga_metadata = json.loads(resp_manga.text)
    else:
        print('Failure. Status code: ', resp_manga.status_code)
        os.quit()
        sys.exit()
    
    chapter_list = []

    # get chapters in preferred language
    for chapter_key in manga_metadata['chapter'].keys():
        chapter = manga_metadata['chapter'][chapter_key]
        if chapter['lang_name'] in ALLOWED_LANGS:
            chapter_info = (chapter['lang_name'], chapter_key)
            chapter_list.append(chapter_info)
    
    #if no starting range is specified, ask for it
    start_chap = None
    if my_args.cstart is None:
        start_x = int(input("Starting chapter: "))
        start_chap = start_x
    else:
        start_chap = int(my_args.cstart)

    # if not end range is specified, ask for it
    stop_chap = None
    if my_args.cstop is None:
        stop_x = int(input("Starting chapter: "))
        stop_chap = stop_x
    else:
        stop_chap = int(my_args.cstop)


    # group by laanguage
    for key, group in itertools.groupby(chapter_list, operator.itemgetter(0)):
        lang_chapters = list(group)
        lang_chapters.reverse()
        lang_chapters = lang_chapters[start_chap-1:stop_chap]
        for chapter in lang_chapters:
            download_chapter(chapter[0], chapter[1])



if __name__ == '__main__':
    main()
