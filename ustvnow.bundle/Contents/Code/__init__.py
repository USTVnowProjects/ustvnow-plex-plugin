import config
import string
import random
import time
import re
import urllib

TITLE  = "USTVnow"
PREFIX = "/video/ustvnow"
ART = 'art-default.jpg'
ICON = 'icon-default.png'


##########################################################################################
def Start():

    Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    Plugin.AddViewGroup("Images", viewMode="Pictures", mediaType="items")
    ObjectContainer.title1 = TITLE

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0"

##########################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():


    Log.Info('Loaded the main menu from {} {}.'.format(
            Request.Headers['X-Plex-Client-Identifier'],
            Request.Headers['X-Plex-Product']))

    oc = ObjectContainer(no_cache = True)
    linkcode = "plex" + Request.Headers['X-Plex-Client-Identifier']
    linkcode = linkcode.replace("-", "")
    linkurl = config.LINK_URL % linkcode
    token = ""

    # For most setups it is preferable to leave the
    # username blank and follow the linking procedure
    # with the QR code as this will avoid the problem of
    # having credentials assigned at the server level and
    # instead provide the authorization at the device level
    if Prefs["username"]:
        # get the token from user credentials
        token = Login()
    else:
        # get the token from linked device
        token = AuthToken(linkcode)

    if token == None or token == "":
        title = "Link your %s account" % config.BRAND_NAME
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        Link,
                        title = title,
                        thumb = linkurl
                    ),
                title = title,
                thumb = linkurl
            )
        )

    title = "Channel Guide"
    oc.add(
        DirectoryObject(
            key =
                Callback(
                    Guide,
                    title = title,
                    token = token
                ),
            title = title,
            thumb = "http://m.images.ustvnow.com/rk/Guide_a2.png"
        )
    )


    title = "Playing Now"
    oc.add(
        DirectoryObject(
            key =
                Callback(
                    Live,
                    title = title,
                    token = token
                ),
            title = title,
            thumb = "http://m.images.ustvnow.com/rk/LiveTV_a2.png"
        )
    )

    title = "My Recordings"
    oc.add(
        DirectoryObject(
            key =
                Callback(
                    Dvr,
                    title = title,
                    token = token
                ),
            title = title,
            thumb = "http://m.images.ustvnow.com/rk/Dvr_a2.png"
        )
    )

    return oc

##########################################################################################
def Login():
    username = Prefs["username"]
    password = Prefs["password"]
    params = {'username' : username, 'password' : password}
    qstr = urllib.urlencode(params)
    try:
        token = HTTP.Request(config.API_ROOT + '/iphone/1/live/login?' + qstr, timeout=20)
        token = str(token)
        token = token.split('token=', 1)[-1]
        token = token.split('"', 1)[0]
    except:
        token = ""
        Log.Info('Login: failed')

    return token

##########################################################################################
def AuthToken(token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'token' : token, 'rand' : rstr}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/gtv/1/live/getuserbytoken?" + qstr)
    if json["status"] == "success":
        Log.Info('AuthToken: success - {}'.format(json))
        return token
    else:
        Log.Info('AuthToken: failed - {}'.format(json))
        return ""

##########################################################################################
def GetLiveStream(scode, token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'scode': scode, 'token' : token, 'rand' : rstr}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/stream/1/live/view?" + qstr)
    return json["stream"]

##########################################################################################
def GetLiveStreamRedirect(scode, token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'scode': scode, 'token' : token, 'rand' : rstr, 'r' : 'r'}
    qstr = urllib.urlencode(params)
    return config.API_ROOT + "/stream/1/live/view?" + qstr

##########################################################################################
def GetDvrStream(scheduleid, token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'scheduleid': scheduleid, 'token' : token, 'rand' : rstr}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/stream/1/live/play?" + qstr)
    return json["stream"]

##########################################################################################
def GetDvrStreamRedirect(scheduleid, token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'scheduleid': scheduleid, 'token' : token, 'rand' : rstr, 'r' : 'r'}
    qstr = urllib.urlencode(params)
    return config.API_ROOT + "/stream/1/live/play?" + qstr

##########################################################################################
def UpdateDvr(scheduleid, dvraction, token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'scheduleid': scheduleid, 'token' : token, 'action' : dvraction, 'rand' : rstr, 'return' : 'json'}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/gtv/1/live/updatedvr?" + qstr)
    return json

##########################################################################################
@route(PREFIX + '/listchannels')
def ListChannels(token):
    params = {'token' : token}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/gtv/1/live/listchannels?" + qstr)
    return json["results"]["streamnames"]

##########################################################################################
@route(PREFIX + '/channelguide')
def ChannelGuide(scode, token, rand):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'c': scode, 'token' : token, 'rand' : rstr}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/gtv/1/live/channelguide?" + qstr)
    return json["results"]

##########################################################################################
@route(PREFIX + '/playingnow')
def PlayingNow(token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'token' : token, 'rand' : rstr}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/gtv/1/live/playingnow?" + qstr)
    return json["results"]

##########################################################################################
@route(PREFIX + '/recordings')
def Recordings(token):
    rstr = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    params = {'token' : token, 'rand' : rstr}
    qstr = urllib.urlencode(params)
    json = JSON.ObjectFromURL(config.API_ROOT + "/gtv/1/live/viewdvrlist?" + qstr)
    return json["results"]

##########################################################################################
@route(PREFIX + '/link')
def Link(title, thumb):
    message = "Scan, link and re-enter PLEX"
    oc = ObjectContainer(title2 = title, no_cache=True)
    oc.add(CreatePhotoObject(
        url=thumb, title=message
        ))
    return oc

@route(PREFIX + '/upgrade')
##########################################################################################
def ShowErrorUpgrade(title, token):

    if token:
        message = "Upgrade now at www.%s.com to view this channel" % config.BRAND
    else:
        message = "Link your account by scanning the QR code" % config.BRAND

    return ObjectContainer(
        header = title,
        message = message,
        replace_parent = True,
        no_history = True,
    )

##########################################################################################
@route(PREFIX + '/live')
def Live(title, token):

    oc = ObjectContainer(title2 = title, no_cache=True)
    programs = PlayingNow(token = token)
    for prg in programs:
        scode = prg["scode"]
        sname = prg["stream_code"]
        callsign = prg["callsign"]
        stream_origin = prg["stream_origin"]
        srsid = prg["seriesid"]
        domain = re.match('.+\.(.+)\.com', stream_origin).group(1)
        now = int(time.time())
        rand = now - (now % 120)
        thumbUrl = "http://m.poster.static-%s.com/%s/%s/sh/high/snapshot?rand=%i" % (domain, srsid, callsign, rand)

        if prg["content_allowed"] == True:
            oc.add(CreateLiveVideoClip(
                scode = scode,
                token = token,
                title = sname + " - " + prg["title"],
                summary = prg["synopsis"],
                thumb = thumbUrl
            ))
        else:
            oc.add(DirectoryObject(
                key =
                    Callback(
                        ShowErrorUpgrade,
                        title = "Upgrade - " + sname + " - " + prg["title"],
                        token = token
                    ),
                title = sname + " - " + prg["title"],
                thumb = thumbUrl
            ))

    if len(oc) < 1:
        return NoProgramsFound(oc, title)
    return oc


##########################################################################################
@route(PREFIX + '/dvr')
def Dvr(title, token):

    oc = ObjectContainer(title2 = title, no_cache=True)
    recordings = Recordings(token = token)
    for recitem in recordings:

        if recitem["event_inprogress"] == 0:
            scheduleid = recitem["scheduleid"]
            sname = recitem["sname"]
            callsign = recitem["callsign"]
            srsid = recitem["srsid"]
            recordedon = recitem["recordedon"]
            domain = recitem["dvrdomain"]
            episode_title = recitem["episode_title"]
            episode_season = recitem["episode_season"]
            episode_number = recitem["episode_number"]

            if episode_title == "":
                if episode_season==0 and episode_number==0:
                    episode_title = "Recorded on " + recitem["recordedon"]
                else:
                    episode_title = "Season %i Episode %i" % (episode_season, episode_number)

            now = int(time.time())
            rand = now - (now % 120)
            thumbUrl = "http://m.poster.static-%s.com/%s/%s/sh/high/generic?rand=%i" % (domain, srsid, callsign, rand)

            oc.add(CreateDvrVideoClip(
                scheduleid = scheduleid,
                token = token,
                title = sname + " - " + recitem["title"] + " - " + episode_title,
                summary = recordedon + " - " + recitem["description"],
                thumb = thumbUrl
            ))

    if len(oc) < 1:
        return NoProgramsFound(oc, title)
    return oc


##########################################################################################
@route(PREFIX + '/guide')
def Guide(title, token):

    oc = ObjectContainer(title2 = title, no_cache=True)
    channels = ListChannels(token = token)
    for ch in channels:
        scode = ch["scode"]
        sname = ch["sname"]
        callsign = ch["callsign"]
        thumbUrl = "http://tvdata.%s.com/chn-logos/poster-color/medium/%s_wbg.png" % (config.BRAND, callsign)

        oc.add(DirectoryObject(
            key =
                Callback(
                    Channel,
                    title = sname,
                    scode = scode,
                    callsign = callsign,
                    token = token,
                    rand = time.time()
                ),
            title = sname,
            summary = sname,
            thumb = thumbUrl
        ))
    if len(oc) < 1:
        return NoProgramsFound(oc, title)
    return oc



##########################################################################################
@route(PREFIX + '/channel')
def Channel(title, scode, callsign, token, rand):

    oc = ObjectContainer(title2 = title, no_cache=True)

    now = int(time.time())
    rand = now - (now % 120)
    programs = ChannelGuide(scode =scode, token = token, rand = time.time())
    for prg in programs:

        stream_origin = prg["stream_origin"]
        srsid = prg["srsid"]
        domain = re.match('.+\.(.+)\.com', stream_origin).group(1)

        if prg["event_inprogress"] == 1:
            thumbUrl = "http://m.poster.static-%s.com/%s/%s/sh/high/snapshot?rand=%i" % (domain, srsid, callsign, rand)

            if prg["content_allowed"] == True:
                oc.add(CreateLiveVideoClip(
                    scode = scode,
                    token = token,
                    title = "NOW AIRING - " + prg["title"],
                    summary = prg["synopsis"],
                    thumb = thumbUrl
                ))
            else:
                oc.add(DirectoryObject(
                    key =
                        Callback(
                            ShowErrorUpgrade,
                            title = "Upgrade - " + title + " - " + prg["title"],
                            token = token
                        ),
                    title = "NOW AIRING - " + prg["title"],
                    thumb = thumbUrl
                ))

        else:
            thumbUrl = "http://m.poster.static-%s.com/%s/%s/sh/high/generic?rand=%i" % (domain, srsid, callsign, rand)
            rectitle = "REC [ON]"

            if prg["dvraction"] == "add":
                rectitle = "REC [OFF]"

            oc.add(DirectoryObject(
                key =
                    Callback(
                        RecordProgram,
                        title = prg["title"],
                        scheduleid = prg["scheduleid"],
                        dvraction = prg["dvraction"],
                        token = token
                    ),
                title = rectitle + " - " + prg["title"],
                summary = prg["synopsis"],
                thumb = thumbUrl
            ))


    if len(oc) < 1:
        return NoProgramsFound(oc, title)

    return oc


##########################################################################################
@route(PREFIX + '/recordProgram')
def RecordProgram(title, scheduleid, dvraction, token):

    json = UpdateDvr(scheduleid, dvraction, token)

    if json["result"] == "success":
        Log.Info('RecordProgram: success - {}'.format(json))
        if dvraction == "add":
            message = "Program marked for Recording"
        else:
            message = "Program canceled for Recording"
    else:
        Log.Info('RecordProgram: failed - {}'.format(json))
        if dvraction == "add":
            message = "Failed to mark for Recording"
        else:
            message = "Failed to cancel for Recording"

    return ObjectContainer(
        header = title,
        message = message,
        replace_parent = True,
        no_history = True,
    )


##########################################################################################
def NoProgramsFound(oc, title):

    oc.header  = title
    oc.message = "No programs found."
    return oc

####################################################################################################
@route(PREFIX + '/createvideoclipobject', container=bool )
def CreateVideoClipObject(url, title, summary, thumb, container = False, **kwargs):
    vco = VideoClipObject(
        rating_key = title,
        key = Callback(CreateVideoClipObject, url = url, title = title, summary = summary, thumb = thumb, container = True),
        url = url,
        title = title,
        summary = summary,
        thumb = thumb,
        items = [
            MediaObject(
                parts = [
                    PartObject(
                        key = HTTPLiveStreamURL(url)
                    )
                ],
                optimized_for_streaming = True
            )
        ]
    )

    if container:
        return ObjectContainer(objects = [vco])
    else:
        return vco

####################################################################################################
@route(PREFIX + '/create-photo-object', include_container=bool)
def CreatePhotoObject(title, url, include_container=False, *args, **kwargs):

    photo_object = PhotoObject(
        key=Callback(CreatePhotoObject,
            title=title, url=url, include_container=True),
        rating_key=url,
        title=title,
        thumb=url,
        items=[MediaObject(parts=[PartObject(key=url)])]
        )

    if include_container:
        return ObjectContainer(objects=[photo_object])
    return photo_object


####################################################################################################
@route(PREFIX + '/createlivevideoclip', container=bool )
def CreateLiveVideoClip(scode, token, title, summary, thumb, container = False, **kwargs):
    vco = VideoClipObject(
        rating_key = scode,
        key = Callback(CreateLiveVideoClip, scode = scode, token = token, title = title, summary = summary, thumb = thumb, container = True),
        title = title,
        summary = summary,
        thumb = thumb,
        items = [
            MediaObject(
                parts = [
                    PartObject(
                        #key = HTTPLiveStreamURL(url)
                        key=HTTPLiveStreamURL(Callback(PlayLiveVideo, scode = scode, token = token))
                    )
                ],
                optimized_for_streaming = True
            )
        ]
    )

    if container:
        return ObjectContainer(objects = [vco])
    else:
        return vco


@indirect
@route(PREFIX + '/playlive.m3u8')
def PlayLiveVideo(scode, token):
    url = GetLiveStreamRedirect(scode, token)
    return IndirectResponse(VideoClipObject, key = url)



####################################################################################################
@route(PREFIX + '/createdvrvideoclip', container=bool )
def CreateDvrVideoClip(scheduleid, token, title, summary, thumb, container = False, **kwargs):
    vco = VideoClipObject(
        rating_key = scheduleid,
        key = Callback(CreateDvrVideoClip, scheduleid = scheduleid, token = token, title = title, summary = summary, thumb = thumb, container = True),
        title = title,
        summary = summary,
        thumb = thumb,
        items = [
            MediaObject(
                parts = [
                    PartObject(
                        #key = HTTPLiveStreamURL(url)
                        key=HTTPLiveStreamURL(Callback(PlayDvrVideo, scheduleid = scheduleid, token = token))
                    )
                ],
                optimized_for_streaming = True
            )
        ]
    )

    if container:
        return ObjectContainer(objects = [vco])
    else:
        return vco


@indirect
@route(PREFIX + '/playdvr.m3u8')
def PlayDvrVideo(scheduleid, token):
    url = GetDvrStreamRedirect(scheduleid, token)
    return IndirectResponse(VideoClipObject, key = url)


