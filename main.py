from xbmcswift2 import Plugin,ListItem
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

    url = 'http://my.tvguide.co.uk/channellisting.asp?ch=%s' % number
        
    item = {
    'label': '[COLOR yellow][B]%s[/B][/COLOR] [COLOR red][B]Listing[/B][/COLOR]' % (name),
    'path': plugin.url_for('listing', name=name,number=number,url=url),
    'is_playable': False,
    }
    items.append(item)
        
    return items
    
def local_time(ttime):
    from datetime import datetime, timedelta
    from dateutil import tz
    

    from_zone = tz.gettz('UTC')
    #log2(from_zone)
    to_zone = tz.gettz()
    match = re.search(r'(.{1,2}):(.{2})(.{2})',ttime)
    if match:
        hour = int(match.group(1))
        min = int(match.group(2))
        ampm = match.group(3)
        if ampm == "pm":
            if hour < 12:
                hour = hour + 12
                hour = hour % 24
        else:
            if hour == 12:
                hour = 0
        
        #log(hour)
        utc = datetime.utcnow()
        #utc = utc.replace(hour=hour,minute=min,tzinfo=from_zone)
        utc = utc.replace(hour=hour,minute=min)

        # get the local timezone offset in seconds
        is_dst = time.daylight and time.localtime().tm_isdst > 0
        utc_offset = - (time.altzone if is_dst else time.timezone) - 3600
        td_local = timedelta(seconds=utc_offset)

        local = utc + td_local
        
        #local = utc.astimezone(to_zone)
        ttime = "%02d:%02d" % (local.hour,local.minute)

    return ttime
                
@plugin.route('/listing/<name>/<number>/<url>')
def listing(name,number,url):
    r = requests.get(url)
    html = r.text

    items = []
    
    match = re.search(r'<a href=\'(.*?)\'>previous</a>.*?<a href=\'(.*?)\'.*?>next</a>',html,flags=(re.DOTALL | re.MULTILINE))
    if match:
        next = 'http://my.tvguide.co.uk%s' % match.group(1)
        previous = 'http://my.tvguide.co.uk%s' % match.group(2)
        next_day = ''
        match = re.search(r'cTime=(.*?) ',next)
        if match:
            next_day = match.group(1)
        previous_day = ''
        match = re.search(r'cTime=(.*?) ',previous)
        if match:
            previous_day = match.group(1)
        next_label = '>> [B]Next[/B] (%s) >>' % previous_day
        previous_label = '<< [B]Previous[/B] (%s) <<' % next_day
        items.append({'label': previous_label, 'path' : plugin.url_for('listing', name=name.encode("utf8"),number=number,url=previous)})
        items.append({'label': next_label, 'path' : plugin.url_for('listing', name=name.encode("utf8"),number=number,url=next)})

    tables = html.split('<table')

    for table in tables:
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
            
        ttime = ''
        title = ''
        plot = ''
        match = re.search(r'<span class="season">(.*?) </span>.*?<span class="programmeheading" >(.*?)</span>.*?<span class="programmetext">(.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            ttime = match.group(1)
            title = match.group(2)
            plot = match.group(3)
            
            ttime = local_time(ttime)

            
        path = plugin.url_for('play', channel=number,title=title.encode("utf8"),season=season,episode=episode)
        
        if title:
            
            if  plugin.get_setting('channel_name') == 'true':
                if plugin.get_setting('show_plot') == 'true':
                    label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR] %s" % (name,ttime,title,plot)
                else:
                    label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR]" % (name,ttime,title)
            else:
                if plugin.get_setting('show_plot') == 'true':
                    label = "%s [COLOR orange][B]%s[/B][/COLOR] %s" % (ttime,title,plot)
                else:
                    label = "%s [COLOR orange][B]%s[/B][/COLOR]" % (ttime,title)
            item = {'label': label,  'thumbnail': thumb, 'info': {'plot':plot, 'season':season, 'episode':episode, 'genre':genre}}
            if path:
                item['path'] = path
            else:
                item['is_playable'] = False,
            items.append(item)
   

    plugin.set_content('episodes')    
    plugin.set_view_mode(51)
    return items
    
def channel_listing_item(name,number):
    thumb = "http://my.tvguide.co.uk/channel_logos/60x35/%s.png" % number
    url = 'http://my.tvguide.co.uk/channellisting.asp?ch=%s' % number
    item = {'label': name, 'thumbnail': thumb, 'path': plugin.url_for('listing', name=name.encode("utf8"),number=number, url=url)}
    return item
    
def load_channels():
    if plugin.get_setting('channels_reload') == 'true':
        plugin.set_setting('channels_reload','false')
        r = requests.get('http://www.tvguide.co.uk/')
        html = r.text
    
        match = re.search(r'<select name="channelid">(.*?)</select>',html,flags=(re.DOTALL | re.MULTILINE))
        if not match:
            return
        
        f = xbmcvfs.File('special://userdata/addon_data/plugin.video.tvlistings/template.ini','w')
        f.write("# WARNING Make a copy of this file.\n# It will be overwritten on the next channel reload.\n[plugin.video.template]\n")
        
        channels = re.findall(r'<option value=(.*?)>(.*?)</option>',match.group(1),flags=(re.DOTALL | re.MULTILINE))

        channel_number = plugin.get_storage('channel_number')
        for channel in channels:
            name = channel[1]
            number = channel[0]
            channel_number[number] = name
            line = "%s=\n" % name
            f.write(line.encode("utf8"))
        f.close()
    
@plugin.route('/channels/<favourites>')
def channels(favourites):
    items = []
    channel_number = plugin.get_storage('channel_number')
    favourite_channels = plugin.get_storage('favourite_channels')
    if favourites == 'true':
        for number in favourite_channels:
            name = favourite_channels[number]
            items.append(channel_listing_item(name,number))            
    else:
        for number in channel_number:
            name = channel_number[number]
            items.append(channel_listing_item(name,number))

    plugin.set_view_mode(51)
    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items                


    
@plugin.route('/now_next/<favourites>')
def now_next(favourites):
    r = requests.get('http://www.tvguide.co.uk/mobile/')
    html = r.text
    
    channels = html.split('<div class="div-channel-progs">')
    videos = []
    favourite_channels = plugin.get_storage('favourite_channels')
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
            if favourites == 'true':
                if not channel_number in favourite_channels:
                    continue

        start = ''
        program = ''
        next_start = ''
        next_program = ''
        after_start = ''
        after_program = ''
        match = re.search(r'<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>.*?<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>.*?<div class="div-time">(.*?)</div>.*?<div class="div-title".*?">(.*?)</div>', channel,flags=(re.DOTALL | re.MULTILINE))
        if match:
            start = local_time(match.group(1))
            program = match.group(2)
            next_start = local_time(match.group(3))
            next_program = match.group(4)
            after_start = local_time(match.group(5))
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
        
        if favourites == 'true':
            if channel_number in favourite_channels:
                items.append(item)
        else:
            items.append(item)
       
       
    plugin.set_view_mode(51)
    return items
   
@plugin.route('/all_favourites')
def all_favourites():
    favourite_channels = plugin.get_storage('favourite_channels')
    channel_number = plugin.get_storage('channel_number')
    for channel in channel_number:
        favourite_channels[channel] = channel_number[channel]
    
@plugin.route('/no_favourites')
def no_favourites():
    favourite_channels = plugin.get_storage('favourite_channels')
    favourite_channels.clear()

    
@plugin.route('/add_favourite/<name>/<number>')
def add_favourite(name,number):
    favourite_channels = plugin.get_storage('favourite_channels')
    favourite_channels[number] = name

@plugin.route('/remove_favourite/<name>/<number>')
def remove_favourite(name,number):
    favourite_channels = plugin.get_storage('favourite_channels')
    favourite_channels.pop(number)
  
@plugin.route('/set_favourites')
def set_favourites():
    top_items = []
    top_items.append({'label': '[COLOR green][B]ALL[/B][/COLOR]','path': plugin.url_for('all_favourites')})
    top_items.append({'label': '[COLOR red][B]NONE[/B][/COLOR]','path': plugin.url_for('no_favourites')})
    
    channel_number = plugin.get_storage('channel_number')
    favourite_channels = plugin.get_storage('favourite_channels')
    items = []
    selected =  plugin.get_setting('selected')
    for channel in channel_number:
        number = channel
        name = channel_number[number]
        if channel in favourite_channels:
            label = '[COLOR yellow][B]%s[/B][/COLOR]' % name
            path = plugin.url_for('remove_favourite', name=name.encode("utf8"), number=number)
        else:
            label = '%s' % name
            path = plugin.url_for('add_favourite', name=name.encode("utf8"), number=number)

        item = {'label':label}
        item['path'] = path 
        item['thumbnail'] = "http://my.tvguide.co.uk/channel_logos/60x35/%s.png" % number
        items.append(item)
        
    sorted_items = sorted(items, key=lambda item: re.sub('\[.*?\]','',item['label']))
    top_items.extend(sorted_items)
    return top_items
    
@plugin.route('/store_channels')
def store_channels():
    ini_files = [plugin.get_setting('ini_file1'),plugin.get_setting('ini_file2')]
    
    for ini in ini_files:
        try:
            f = xbmcvfs.File(ini)
            items = f.read().splitlines()
            f.close()
            addon = 'nothing'
            for item in items:
                if item.startswith('['):
                    addon = item.strip('[] \t')
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
            #log(match)
            #continue
            match = re.search(r'(.*?)</span>.*?<span class="datetime">(.*?)</span><br>.*?<b><span class="season">Season (.*?) </span>.*?<span class="season">Episode (.*?) of (.*?)</span>',table,flags=(re.DOTALL | re.MULTILINE))
            if match:
                channel = match.group(1)
                date = match.group(2)
                season = match.group(3)
                episode = match.group(4)
                total = match.group(5)
                
                #log(channel)
                #log(date)
                #log(season)
                #log(episode)
                #log(total)
                continue
        #continue
        match = re.search(r'<span property="description"',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            match = re.search(r'(.*?)</span>.*?<span property="description" content="(.*?)"></span>',table,flags=(re.DOTALL | re.MULTILINE))
            if match:
                episode_title =  match.group(1)
                plot =  match.group(2)
                #log(episode_title)
                #log(plot)
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
    load_channels()
    items = [  
    {
        'label': '[COLOR green][B]Favourites[/B][/COLOR]: [COLOR yellow]All Next After[/COLOR] popular',
        'path': plugin.url_for('now_next', favourites='true' ),

    } ,  
    {
        'label': '[COLOR green][B]Favourites[/B][/COLOR]: [COLOR orange]Channel Listings[/COLOR] full',
        'path': plugin.url_for('channels', favourites='true' ),

    } ,      
    {
        'label': '[COLOR red][B]All[/B][/COLOR]: [COLOR yellow]Now Next After[/COLOR] popular',
        'path': plugin.url_for('now_next', favourites='false'),

    } ,  
    {
        'label': '[COLOR red][B]All[/B][/COLOR]: [COLOR orange]Channel Listings[/COLOR] full',
        'path': plugin.url_for('channels', favourites='false'),

    } ,        
    {
        'label': '[B]Favourites[/B]: Toggle',
        'path': plugin.url_for('set_favourites' ),

    } ,     
    ]
    return items
    
if __name__ == '__main__':
    plugin.run()
