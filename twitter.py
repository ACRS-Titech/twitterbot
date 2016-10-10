#!/usr/bin/env python
#-*- coding:utf-8 -*-

from tweepy import *
import urllib
import sys
import datetime
import re
from PIL import Image
import cv2
import sys
import os.path
import numpy as np
import skimage
import copy
import scipy
import twitter_getinfo
import urllib


# エンコード設定
reload(sys)
sys.setdefaultencoding('utf-8')

def get_oauth():
	consumer_key = "RdQyuTxK0dJViYD5wd6Sa0Cx2"
	consumer_secret = "AvRlaTUb2GZwZGQ2wEsGsdgXEfiZDjCZ7CDtTM2ZIOmypNvhLz"
	access_key = "762464297616232448-cz7wOZDzwc1M7jxdxOUqKfwZGrKemUz"
	access_secret = "wv9aXpHhc7kd8UEsgmuf7PRPrFew21MXX2xnjuwcw1qbG"
	auth = OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_key, access_secret)
	return auth



class StreamListener(StreamListener):
    # ツイートされるたびにここが実行される
    def on_status(self, status):
        if status.in_reply_to_screen_name=='ACRSdemo':
            if status.entities.has_key('media') :
                text = re.sub(r'@ACRSdemo ', '', status.text)
                text = re.sub(r'(https?|ftp)(://[\w:;/.?%#&=+-]+)', '', text)
                medias = status.entities['media']
                m =  medias[0]
                media_url = m['media_url']
                print media_url
                now = datetime.datetime.now()
                time = now.strftime("%H%M%S")
                filename = '{}.jpg'.format(time)
                try:
                    urllib.urlretrieve(media_url, filename)
                except IOError:
                    print "Failed"
                frame = cv2.imread(filename)
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                #CameraLocation=twitter_getinfo.getcamerainfo()
                print filename
                print "Maching Start"
                lat,lon,name,inf=twitter_getinfo.get_info(filename)
                print "Maching Finished"
                print lat
                print lon
                print name
                print inf
                key = "AIzaSyCmYl1wwZLoOslolQCPsH3ZMaN52yAVnO4"
                lat = str(lat)
                log = str(lon)
                print "URL setting"
                url ="http://maps.google.com/maps/api/staticmap?center=" +lat + "," + log + "&zoom=15.5&size=600x400&markers=" +lat + "%2C" + log + "&sensor=false&key=" + key+"&language=en"

                #LandscapeName = twitter_getinfo.getLandScapeinfo()
                #centername=KandaMyojin
                #centername = urllib.quote(centername)
                print url
                mapapi = str(url)
                print mapapi
                message = '.@'+status.author.screen_name+' Landscame is '+str(name)+', CameraLocation is '+str(lat)+' , '+str(lon) +' ' + str(mapapi)
                print message
                #massege = str(massege)
                #message = message.decode("utf-8")
                print message
                try:
                    #画像をつけてリプライ
                    #api.update_status(str(message))
                    api.update_with_media(filename, status=message, in_reply_to_status_id=status.id)
                    api.update_with_media
                except TweepError, e:
                    print "error response code: " + str(e.response.status)
                    print "error message: " + str(e.response.reason)


# streamingを始めるための準備
auth = get_oauth()
api = API(auth)
stream = Stream(auth, StreamListener(), secure=True)
print "Start Streaming!"
stream.userstream()


