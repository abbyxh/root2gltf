#!/usr/bin/env python
# coding: utf-8

from dd4hep import Detector
import re
from argparse import ArgumentParser
import pprint
import json

parser = ArgumentParser()

parser.add_argument(
    "--compact", help="DD4hep compact description xml", required=True
)
parser.add_argument(
    "--max_depth", help="Maximum traversal depth of the detector tree", default=10, type=int,
)
parser.add_argument(
    "--config_path", help="Location of produced config file", default='nothing', type=str,
)
parser.add_argument(
    "--hide_list", help="List of detector geometries that aren't shown", default='', type=str, nargs='+'
)

args = parser.parse_args()
print(args.hide_list)
theDetector = Detector.getInstance()
theDetector.fromXML(args.compact)
start = theDetector.world()

def process_name(raw_name):
    name = re.sub(r"\d+", ".*", raw_name)
    return name

def tree(detElement, depth, maxDepth):
    nd = {}
    depth += 1
    children = detElement.children()
    for raw_name, child in children:
        if depth > maxDepth:
            tree(child, depth, maxDepth)
        else:
            dictionary = tree(child, depth, maxDepth)
            nd.update({raw_name: dictionary})
    return nd


def post_processing(obj, main_parts, hidden, subParts={}, sublist= [], hide_children= []):
    for k, v in obj.items():
        if k in main_parts:
            y = re.search(f'{hidden}', f'{k}')
            if y == None:
                #removes envelopes from being featured in the final geometry
                sublist = [f'({k}_(?!envelope))\\w+|({k}(?!_))\w+']  
                outer_list = []
                outer_list.append(sublist)
                outer_list.append(0.8)
                subParts.update({str(k): outer_list})
                post_processing(v, main_parts, hidden, subParts, sublist)

            else:
                hide_children.append(f'{k}')
                post_processing(v, main_parts, hidden, subParts, sublist, hide_children)
                
        else:
            k_new = process_name(f"{k}\\w+")
            x = re.search("module|stave|layer|Calorimeter|component", k_new)
            if k_new not in sublist and x == None:
                sublist.append(f'{k_new}')
            post_processing(v, main_parts, hidden, subParts, sublist, hide_children)
    return subParts, hide_children
            
detector_dict = tree(start, 0, args.max_depth)
subPart_processed, hidden_children = post_processing(detector_dict, list(detector_dict.keys()), '|'.join(args.hide_list[0].split(", ")))

final_dict = {"childrenToHide": hidden_children,
              "subParts": subPart_processed,
              "maxLevel": 3}

pprint.pprint(final_dict)
with open(args.config_path, "w") as outfile: 
    json.dump(final_dict, outfile, indent=4)