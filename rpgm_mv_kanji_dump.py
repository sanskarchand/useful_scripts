#!/usr/bin/env python
import nagisa
import argparse
import json
import os
import sys
import collections

KANJI_RANGE = (0x4E00, 0x9FBF)
#PUNCTUATION_RANGE = (0x3000, 0x303F)
#HIRAGANA_RANGE = (0x3040, 0x309F)
#KATAKANA_RANGE = (0x30A0, 0x30FF)

parser = argparse.ArgumentParser(description="Extract sentences from RPGM MV data directories")
parser.add_argument("datadir", help="data directory (contains .json files)")
parser.add_argument("--verbose", action='store_true', help="print filenames as they are processed")
parser.add_argument("--out",  help="name of the output file. Default is stdout")

# finds k,v pairs (at all levels, with _parent_ as root) for a given k
# puts that node (consider the json a tree) into _nodeList_
def get_nodes_by_name(parent, keyName, nodeList):
    for key in parent.keys():
        if key == keyName:
            nodeList.append(parent[key])
        else:
            # in RPGMV, a 'list' cannot be inside another one of the same
            newParent = parent[key]
            if type(newParent) == dict:
                get_nodes_by_name(newParent, keyName, nodeList)
            elif type(newParent) == list:
                for novaParent in newParent:
                    if type(novaParent) == dict: 
                        get_nodes_by_name(novaParent, keyName, nodeList)

def is_kanji(character):
    return ord(character) >= KANJI_RANGE[0] and ord(character) <= KANJI_RANGE[1]

def get_kanji(nodeList, kanjiCounter):
    #filter out only text events
    textEvents = [event for node in nodeList for event in node if event['code'] == 401]
    
    for each in textEvents:
        japText = each['parameters'][0]
        words = nagisa.tagging(japText)

        for word in words.words:
            for char in  word:
                if not (is_kanji(char)):
                    continue
                
                # add to list of kanji
                kanjiCounter[word] += 1

        

def process_file(filePath, kanjiCounter, verbose):
    if verbose:
        print(f"Processing file  {filePath}")
    nodeList = [] 
    with open(filePath, 'r') as f:
        mapData = json.loads(f.read())

        if type(mapData) == dict and 'events' in mapData.keys():
            get_nodes_by_name(mapData, 'list', nodeList)
            get_kanji(nodeList, kanjiCounter)


       # print(json.dumps(mapData, indent=4))

def main():
    kanjiCounter = collections.Counter()
    args = parser.parse_args()
    datadir = args.datadir
    
    #process only one level in the directory tree
    _, _, filenames = next(os.walk(datadir))    
    

    for fname in filenames:
        filePath = os.path.join(datadir, fname)
        process_file(filePath, kanjiCounter, args.verbose)

    outFile = sys.stdout
    if args.out:
        outFile = open(args.out, "w")
    
    freqSortedKanji = kanjiCounter.most_common()
    for pair in freqSortedKanji:
        line = pair[0] + "\t" + str(pair[1])
        outFile.write(line + "\n")

    if outFile != sys.stdout:
        outFile.close()
    

if __name__ == '__main__':
    main()
