#!/usr/bin/env python
#-*- coding:utf-8 -*-
import final_db

def get_info(imagepath):
    cur,Num=final_db.create_DB()
    lat,lon,name,inf=final_db.compare_img(imagepath,Num,cur)
    return lat, lon, name, inf

def getcamerainfo():
    cameraLoc = "hoge, piyo"
    return cameraLoc

def getLandScapeinfo():
    LandscapeName = "foo"
    return LandscapeName


