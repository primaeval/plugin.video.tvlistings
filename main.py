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
    
def get_tvdb_id(name):
    tvdb_url = "http://thetvdb.com//api/GetSeries.php?seriesname=%s" % name
    r = requests.get(tvdb_url)
    tvdb_html = r.text
    tvdb_id = ''
    tvdb_match = re.search(r'<seriesid>(.*?)</seriesid>', tvdb_html, flags=(re.DOTALL | re.MULTILINE))
    if tvdb_match:
        tvdb_id = tvdb_match.group(1)
    return tvdb_id
  
@plugin.route('/play/<title>/<season>/<episode>')
def play(title,season,episode):
    tvdb_id = get_tvdb_id(title)
    meta_url = "plugin://plugin.video.meta/tv/play/%s/%s/%s/%s" % (tvdb_id,season,episode,'select')
    log(meta_url)
    items = [
    {'label': '%s (%s) %sx%s' % (title,tvdb_id,season,episode),
     'path': meta_url,
     'is_playable': True,
     }
    ]
    return plugin.finish(items)

@plugin.route('/play_channel/<name>')
def play_channel(name):
    channel_player = plugin.get_storage('channels')
    if not name in channel_player:
        return
    path = channel_player[name]
    #xbmc.Player().play(path)
    #return plugin.set_resolved_url(path)
    items = [
    {'label': '%s %s' % (name,path),
     'path': path,
     'is_playable': True,
     }
    ]
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
            detail = url=match.group(1).encode("utf8")
            
        
            
        season = ''
        episode = ''
        match = re.search(r'<b><span class="season">Season (.*?) </span> <span class="season">Episode (.*?) of (.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            season = match.group(1)
            episode = match.group(2)
        
        genre = ''
        match = re.search(r'<span class="tvchannel">Category </span><span class="programmetext">(.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            genre = match.group(1)
            
        time = ''
        title = ''
        plot = ''
        match = re.search(r'<span class="season">(.*?) </span>.*?<span class="programmeheading" >(.*?)</span>.*?<span class="programmetext">(.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            time = match.group(1)
            title = match.group(2)
            plot = match.group(3)
            
        if title and season and episode:
            path = plugin.url_for('play', title=title,season=season,episode=episode)
        #tvdb_id = get_tvdb_id(title)
        #meta_url = "plugin://plugin.video.meta/tv/play/%s/%s/%s/%s" % (tvdb_id,season,episode,'select')
        
        if title:
            label = "%s [COLOR orange][B]%s[/B][/COLOR] %s" % (time,title,plot)
            item = {'label': label,  'thumbnail': thumb, 'info': {'plot':plot, 'season':season, 'episode':episode, 'genre':genre}}
            if path:
                item['path'] = path
            else:
                item['is_playable'] = False,
            items.append(item)
   

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
    #channel_player = plugin.get_storage('channels')
    
    
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
            
        item = {'label':label,'icon':img_url,'thumbnail':img_url}
        item['path'] = plugin.url_for('play_channel', name=name)
        #item['is_playable'] = False
        #if name in channel_player:
        #    item['is_playable'] = True
        #    item['path'] = channel_player[name]
        
        items.append(item)
        
    plugin.set_view_mode(51)
    return items

@plugin.route('/store_channels')
def store_channels():
    channels = plugin.get_storage('channels')
    #channels['BBC1 London'] = 'plugin://plugin.video.iplayerwww/?url=bbc_one_hd&mode=203&name=BBC+One&iconimage=special%3A%2F%2Fhome%2Faddons%2Fplugin.video.iplayerwww%2Fmedia%2Fbbc_one.png&description=&subtitles_url=&logged_in=False'
    
    ini_files = [plugin.get_setting('ini_file1'),plugin.get_setting('ini_file2')]
    
    for ini in ini_files:
        log(ini)
        try:
            f = xbmcvfs.File(ini)
            b = f.read()
            log2(b)
            f.close()
            items = re.findall(r'(.*?)=(.*?)\r\n',b)
            for item in items:
                log2(item)
                name = item[0]
                url = item[1]
                if not name.startswith('#'):
                    channels[name] = url
        except:
            pass
    
    #http://my.tvguide.co.uk/titlesearch.asp?title=doctor%20who

@plugin.route('/search/<name>')
def search_for(name):
    if not name:
        return
    url = 'http://my.tvguide.co.uk/titlesearch.asp?title=%s' % name
    
    r = requests.get(url)
    html = r.text
    #log2(html)
    #return
    
    tables = html.split('<span class="tvchannel">')
    items = []
    for table in tables:
        log(table)
        #continue
        #channel = ''
        #date = ''
        match = re.search(r'<span class="datetime">(.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            log(match)
            #continue
            match = re.search(r'(.*?)</span>.*?<span class="datetime">(.*?)</span><br>.*?<b><span class="season">Season (.*?) </span>.*?<span class="season">Episode (.*?) of (.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
            if match:
                channel = match.group(1)
                date = match.group(2)
                season = match.group(3)
                episode = match.group(4)
                total = match.group(5)
                
                log(channel)
                log(date)
                log(season)
                log(episode)
                log(total)
                continue
        #continue
        match = re.search(r'<span property="description"',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            match = re.search(r'(.*?)</span>.*?<span property="description" content="(.*?)"></span>',table,flags=(re.DOTALL | re.MULTILINE))
            if match:
                episode_title =  match.group(1)
                plot =  match.group(2)
                log(episode_title)
                log(plot)
                #continue
                label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR red][B]%sx%s[/B][/COLOR] [COLOR orange][B]%s[/B][/COLOR] %s" % (channel,date,season,episode,episode_title,plot)
                item = {'label':label}
                items.append(item)

            
        #continue

   

    return items
    #plugin.set_content('episodes')    
    #plugin.set_view_mode(51)
    return items
    
    
@plugin.route('/search')
def search():
    dialog = xbmcgui.Dialog()
    name = dialog.input('Search for programme', type=xbmcgui.INPUT_ALPHANUM)
    if name:
        return search_for(name)
    
@plugin.route('/')
def index():

    items = [
    {
        'label': 'Search',
        'path': plugin.url_for('search' ),

    } ,      
    {
        'label': 'Now Next After',
        'path': plugin.url_for('now_next' ),

    } ,  
    {
        'label': 'Channel Listings',
        'path': plugin.url_for('channels' ),

    } ,     
    {
        'label': 'Store Channels',
        'path': plugin.url_for('store_channels' ),

    } ,         
    ]
    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items
    
if __name__ == '__main__':
    plugin.run()
