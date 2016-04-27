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

def log2(v):
    xbmc.log(repr(v))

def log(v):
    xbmc.log(re.sub(',',',\n',repr(v)))

@plugin.route('/detail/<url>')
def detail(url):
    r = requests.get('http://my.tvguide.co.uk/channellisting.asp?ch=%s&cTime=4/27/2016%%208:00:00%%20AM&thisTime=&thisDay=' % channel)
    html = r.text
    #log2(html)
    #return
    
    tables = html.split('<table')
    items = []
    for table in tables:
        log(table)
        thumb = ''
        match = re.search(r'background-image: url\((.*?)\)',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            thumb = match.group(1)
        match = re.search(r'<a href="(http://www.tvguide.co.uk/detail/.*?)"',table,flags=(re.DOTALL | re.MULTILINE))
        path = ''
        if match:
            path = plugin.url_for('detail', url=match.group(1))
        
        match = re.search(r'<span class="season">(.*?) </span>.*?<span class="programmeheading" >(.*?)</span>.*?<span class="programmetext">(.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            label = "%s [COLOR orange][B]%s[/B][/COLOR] %s" % (match.group(1),match.group(2),match.group(3))
            items.append({'label': label, 'path': path, 'thumbnail': thumb, 'info': {'plot':match.group(3)}})
   

    plugin.set_content('episodes')    
    plugin.set_view_mode(51)
    return items
    
@plugin.route('/listing/<channel>')
def listing(channel):
    r = requests.get('http://my.tvguide.co.uk/channellisting.asp?ch=%s&cTime=4/27/2016%%208:00:00%%20AM&thisTime=&thisDay=' % channel)
    html = r.text
    #log2(html)
    #return
    
    tables = html.split('<table')
    items = []
    for table in tables:
        #log(table)
        thumb = ''
        match = re.search(r'background-image: url\((.*?)\)',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            thumb = match.group(1)
        match = re.search(r'<a href="(http://www.tvguide.co.uk/detail/.*?)"',table,flags=(re.DOTALL | re.MULTILINE))
        path = ''
        if match:
            path = plugin.url_for('detail', url=match.group(1).encode("utf8"))
            
        season = ''
        episode = ''
        match = re.search(r'<b><span class="season">Season (.*?) </span> <span class="season">Episode (.*?) of (.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            season = match.group(1)
            episode = match.group(2)
        
        match = re.search(r'<span class="season">(.*?) </span>.*?<span class="programmeheading" >(.*?)</span>.*?<span class="programmetext">(.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            label = "%s [COLOR orange][B]%s[/B][/COLOR] %s" % (match.group(1),match.group(2),match.group(3))
            items.append({'label': label, 'path': path, 'thumbnail': thumb, 'info': {'plot':match.group(3), 'season':season, 'episode':episode}})
   

    plugin.set_content('episodes')    
    plugin.set_view_mode(51)
    return items
    
@plugin.route('/channels')
def channels():
    r = requests.get('http://www.tvguide.co.uk/')
    html = r.text
    #log2(html)
    
    match = re.search(r'<select name="channelid">(.*?)</select>',html,flags=(re.DOTALL | re.MULTILINE))
    #log(match)
    if not match:
        return
        
    channels = re.findall(r'<option value=(.*?)>(.*?)</option>',match.group(1),flags=(re.DOTALL | re.MULTILINE))
    items = []
    for channel in channels:
        #log(channel)
        items.append({'label': channel[1], 'path': plugin.url_for('listing', channel=channel[0]),})
        
    plugin.set_view_mode(51)
    return items

    
@plugin.route('/now_next')
def now_next():
    r = requests.get('http://www.tvguide.co.uk/mobile/')
    html = r.text
    
    channels = html.split('<div class="div-channel-progs">')
    videos = []
    
    items = []
    for channel in channels:
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
        after_start = ''
        after_program = ''
        match = re.search(r'<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>.*?<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>.*?<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>', channel,flags=(re.DOTALL | re.MULTILINE))
        if match:
            start = match.group(1)
            program = match.group(2)
            next_start = match.group(3)
            next_program = match.group(4)
            after_start = match.group(5)
            after_program = match.group(6)            
            match = re.search('<img.*?>&nbsp;(.*)',program)
            if match:
                program = match.group(1)
            match = re.search('<img.*?>&nbsp;(.*)',next_program)
            if match:
                next_program = match.group(1)
            match = re.search('<img.*?>&nbsp;(.*)',after_program)
            if match:
                after_program = match.group(1)

        channel_name = plugin.get_setting('channel_name')
        if  channel_name == 'true':
            label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR] %s [COLOR white][B]%s[/B][/COLOR] %s [COLOR grey][B]%s[/B][/COLOR]" % (name,start,program,next_start,next_program,after_start,after_program)
        else:
            label = "%s [COLOR orange][B]%s[/B][/COLOR] %s [COLOR white][B]%s[/B][/COLOR] %s [COLOR grey][B]%s[/B][/COLOR]" % (start,program,next_start,next_program,after_start,after_program)
        items.append({'label':label,'icon':img_url,'thumbnail':img_url})
        
    plugin.set_view_mode(51)
    return items

@plugin.route('/')
def index():

    items = [
    {
        'label': 'Now Next After',
        'path': plugin.url_for('now_next' ),

    } ,  
    {
        'label': 'Channel Listings',
        'path': plugin.url_for('channels' ),

    } ,     ]
    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items
    
if __name__ == '__main__':
    plugin.run()
