from xbmcswift2 import Plugin
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import os, sys, subprocess
from subprocess import Popen
import json
import re
import time
import xml.etree.ElementTree as etree
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmcgui
import xbmcaddon
import sys
import os

import requests
import re
import urllib,urlparse
import HTMLParser
from trakt import Trakt

plugin = Plugin()


def log(v):
    xbmc.log(re.sub(',',',\n',repr(v)))


@plugin.route('/')
def index():
    r = requests.get('http://www.tvguide.co.uk/mobile/')
    html = r.text
    #log(html)
    #html = HTMLParser.HTMLParser().unescape(html)
    
    channels = html.split('<div class="div-channel-progs">')
    videos = []
    
    items = []
    for channel in channels:
        #log(channel)
        img_url = ''
        name = ''
        img_match = re.search(r'<img class="img-channel-logo" width="50" src="(.*?)"\s*?alt="(.*?) TV Listings" />', channel)
        if img_match:
            img_url = img_match.group(1)
            name = img_match.group(2)

        start = ''
        program = ''
        next_start = ''
        next_program = ''
        match = re.search(r'<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>.*?<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>', channel,flags=(re.DOTALL | re.MULTILINE))
        if match:
            start = match.group(1)
            program = match.group(2)
            next_start = match.group(3)
            next_program = match.group(4)
            match = re.search('<img.*?>&nbsp;(.*)',program)
            if match:
                program = match.group(1)
            match = re.search('<img.*?>&nbsp;(.*)',next_program)
            if match:
                next_program = match.group(1)
                
        label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR] %s [COLOR white][B]%s[/B][/COLOR]" % (name,start,program,next_start,next_program)
            
        items.append({'label':label,'icon':img_url,'thumbnail':img_url})

    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items


    
if __name__ == '__main__':
    plugin.run()
