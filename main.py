from xbmcswift2 import Plugin
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import os, sys, subprocess
from subprocess import Popen
import json
import re
import time
import xml.etree.ElementTree as etree


plugin = Plugin()


def log(v):
    xbmc.log(re.sub(',',',\n',repr(v)))


@plugin.route('/')
def index():
       
    items = [
    {
        'label': 'label',
        'path': '',

    } ,  
    ]
    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items


    
if __name__ == '__main__':
    plugin.run()
