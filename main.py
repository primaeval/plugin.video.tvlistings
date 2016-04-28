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
  
@plugin.route('/play/<channel>/<title>/<season>/<episode>')
def play(channel,title,season,episode):
    #log2(channel)
    channel_number = plugin.get_storage('channel_number')
    channel_items = play_channel(channel_number[channel],channel)
    items = []
    tvdb_id = ''
    if int(season) > 0 and int(episode) > 0:
        tvdb_id = get_tvdb_id(title)
    if tvdb_id:
        if season and episode:
            meta_url = "plugin://plugin.video.meta/tv/play/%s/%s/%s/%s" % (tvdb_id,season,episode,'select')
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR red][B]S%sE%s[/B][/COLOR] [COLOR grey](tvdb:%s)[/COLOR]' % (title,season,episode,tvdb_id),
            'path': meta_url,
            'is_playable': True,
             })
        if season:
            meta_url = "plugin://plugin.video.meta/tv/tvdb/%s/%s" % (tvdb_id,season)
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR red][B]S%s[/B][/COLOR] [COLOR grey](tvdb:%s)[/COLOR]' % (title,season,tvdb_id),
            'path': meta_url,
            'is_playable': False,
             })         
        meta_url = "plugin://plugin.video.meta/tv/tvdb/%s" % (tvdb_id)
        items.append({
        'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR grey](tvdb:%s)[/COLOR]' % (title,tvdb_id),
        'path': meta_url,
        'is_playable': False,
         })
    else:
        match = re.search(r'(.*?)\(([0-9]*)\)$',title)
        if match:
            movie = match.group(1)
            year =  match.group(2) #TODO: Meta doesn't support year yet
            meta_url = "plugin://plugin.video.meta/movies/search_term/%s/1" % (movie)
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR grey](movie)[/COLOR]' % (title),
            'path': meta_url,
            'is_playable': False,
             })              
        else:
            meta_url = "plugin://plugin.video.meta/tv/search_term/%s/1" % (title)
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR grey](tvdb:?)[/COLOR]' % (title),
            'path': meta_url,
            'is_playable': False,
             }) 
    #log(items)  
    items.extend(channel_items)
    return items

@plugin.route('/play_channel/<name>/<number>')
def play_channel(name,number):
    if plugin.get_setting('ini_reload') == 'true':
        store_channels()
        plugin.set_setting('ini_reload','false')
    
    addons = plugin.get_storage('addons')
    items = []
    for addon in addons:
        channels = plugin.get_storage(addon)
        if not name in channels:
            continue
        path = channels[name]
        item = {
        'label': '[COLOR yellow][B]%s[/B][/COLOR] [COLOR grey][%s][/COLOR]' % (name,addon),
        'path': path,
        'is_playable': True,
        }
        items.append(item)

    log(number)
    item = {
    'label': '[COLOR yellow][B]%s[/B][/COLOR] [COLOR red][B]Listing[/B][/COLOR]' % (name),
    'path': plugin.url_for('listing', name=name,number=number),
    'is_playable': False,
    }
    items.append(item)
        
    return items
  
@plugin.route('/listing/<name>/<number>')
def listing(name,number):
    #r = requests.get('http://my.tvguide.co.uk/channellisting.asp?ch=%s&cTime=4/27/2016%%208:00:00%%20AM&thisTime=&thisDay=' % channel)
    r = requests.get('http://my.tvguide.co.uk/channellisting.asp?ch=%s' % number)
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
            
        season = '0'
        episode = '0'
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
            
        path = plugin.url_for('play', channel=number,title=title.encode("utf8"),season=season,episode=episode)
        
        if title:
            if  plugin.get_setting('channel_name') == 'true':
                label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR] %s" % (name,time,title,plot)
            else:
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
    channel_number = plugin.get_storage('channel_number')
    for channel in channels:
        #log(channel)
        channel_number[channel[0]] = channel[1]
        items.append({'label': channel[1], 'path': plugin.url_for('listing', name=channel[1].encode("utf8"),number=channel[0])})
        
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
            
        channel_number = '0'
        #log2(channel)
        match = re.search(r'href="http://www\.tvguide\.co\.uk/mobile/channellisting\.asp\?ch=(.*?)"', channel)
        if match:
            channel_number=match.group(1)

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
        item['path'] = plugin.url_for('play_channel', name=name, number=channel_number)
        #item['is_playable'] = False
        #if name in channel_player:
        #    item['is_playable'] = True
        #    item['path'] = channel_player[name]
        
        items.append(item)
        
    plugin.set_view_mode(51)
    return items

@plugin.route('/store_channels')
def store_channels():
    #channels = plugin.get_storage('channels')
    #channels['BBC1 London'] = 'plugin://plugin.video.iplayerwww/?url=bbc_one_hd&mode=203&name=BBC+One&iconimage=special%3A%2F%2Fhome%2Faddons%2Fplugin.video.iplayerwww%2Fmedia%2Fbbc_one.png&description=&subtitles_url=&logged_in=False'
    
    ini_files = [plugin.get_setting('ini_file1'),plugin.get_setting('ini_file2')]
    
    for ini in ini_files:
        #log(ini)
        try:
            f = xbmcvfs.File(ini)
            items = f.read().splitlines()
            #log2(items)
            f.close()
            addon = 'nothing'
            for item in items:
                #log2(item)
                if item.startswith('['):
                    addon = item.strip('[] \t')
                    #log(addon)
                elif item.startswith('#'):
                    pass
                else:
                    name_url = item.split('=',1)
                    if len(name_url) == 2:
                        name = name_url[0]
                        url = name_url[1]
                        channels = plugin.get_storage(addon)
                        channels[name] = url
                        addons = plugin.get_storage('addons')
                        addons[addon] = addon

        except:
            pass


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
