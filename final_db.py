# -*- coding:utf-8 -*-
import os
import sys
from PIL import Image
import numpy as np
import cv2
from matplotlib import pylab as plt
import sqlite3
from PIL.ExifTags import TAGS, GPSTAGS
import pickle
import time

def process_image(imagename,resultname,params="--edge-thresh 10 --peak-thresh 5"):
  if imagename[-3:] != 'pgm':
    # ダウンサンプリングpgmファイルを作成する
    im = np.array(Image.open(imagename).convert('L'))
    im= im[::15, ::15]
    im= Image.fromarray(np.uint8(im))
    im.save('tmp.pgm')
    imagename = 'tmp.pgm'

  cmmd = str("./sift "+imagename+" --output="+resultname+ " "+params)
  os.system(cmmd)
  print 'processed', imagename, 'to', resultname

def read_features_from_file(filename):

  f = np.loadtxt(filename)
  return f[:,:4],f[:,4:]


def match(desc1,desc2):
  desc1 = np.array([d/np.linalg.norm(d) for d in desc1])
  desc2 = np.array([d/np.linalg.norm(d) for d in desc2])

  dist_ratio = 0.6
  desc1_size = desc1.shape

  matchscores = np.zeros(desc1_size[0],'int')
  desc2t = desc2.T

  for i in range(desc1_size[0]):
    dotprods = np.dot(desc1[i,:],desc2t)
    dotprods = 0.9999*dotprods
    indx = np.argsort(np.arccos(dotprods))

    if np.arccos(dotprods)[indx[0]] < dist_ratio * np.arccos(dotprods)[indx[1]]:
      matchscores[i] = int(indx[0])
  return matchscores

# ExifからGPSの取得
def get_exif(file):
  img = Image.open(file)
  df=np.array(Image.open(file))
  exif = img._getexif()

  exif_data = []
  for id, value in exif.items():
    #print 'ID',TAGS.get(id),'\n'
    ID = TAGS.get(id)
    tag = TAGS.get(id, id),value
    #print 'Tag',tag,'\n'
    if ID == 'GPSInfo': 
      exif_data.extend(tag)
  return exif_data

#緯度・経度の算出関数（10進数）
def calculate(GPS):
  lat_ex=GPS[1][2]
  lon_ex=GPS[1][4]
  lat_a=float(lat_ex[0][0]/lat_ex[0][1])
  lat_b=float(lat_ex[1][0]/lat_ex[1][1])
  lat_c=float(lat_ex[2][0]/lat_ex[2][1])
  lat=lat_a+(lat_b/60.0)+(lat_c/60.0/60.0)

  lon_a=float(lon_ex[0][0]/lon_ex[0][1])
  lon_b=float(lon_ex[1][0]/lon_ex[1][1])
  lon_c=float(lon_ex[2][0]/lon_ex[2][1])
  lon=lon_a+(lon_b/60.0)+(lon_c/60.0/60.0)
  return lat,lon

def create_DB():
  #はじめにデータベース作成を行う
  conn = sqlite3.connect(":memory:")
  cur = conn.cursor()
  cur.execute("""CREATE TABLE feature_Point(lat real,lon real,d text,img text,name text);""")
  path='Data_Box'
  imlist = [os.path.join(path,f) for f in os.listdir(path) if f.endswith('.jpg')]
  # データベース格納のための特徴点、GPS情報の算出
  Num=0
  for img_ex in imlist:
    im_grey = np.array(Image.open(img_ex).convert('L'))
    Num=Num+1
    RGB=np.array(Image.open(img_ex))
    name,ext=os.path.splitext(img_ex)
    sname = img_ex+'.sift'
    process_image(img_ex,sname)
    l_db,d_db = read_features_from_file(sname) 
    GPS_db=get_exif(img_ex)
    lat_db,lon_db=calculate(GPS_db)
    print 'Data',lat_db,lon_db
    #データベースへ格納するため、stringへ変換
    img_str=str(im_grey)
    l_db_str=str(l_db)
    d_db_str=unicode(d_db)
    lat_db_str=str(lat_db)
    lon_db_str=str(lon_db)
    print len(d_db)
    print len(d_db[1])
    #Creation for Database
    d_list=[]
    for j in range(len(d_db)):
      df=d_db[j]
      for k in range(len(d_db[1])):
        df_1=int(df[k])
        d_list.append(df_1)
    d_list=str(d_list)
    gray_list=[]
    for j in range(len(im_grey)):
      df=im_grey[j]
      gray=[]
      for k in range(len(im_grey[1])):
        df_1=int(df[k])
        gray.append(df_1)
      gray_list.append(gray)
    gray_list=str(gray_list)
    print 'GRAY',gray_list
    #データベースへ格納
    sql="""INSERT INTO feature_Point(lat,lon) VALUES(?,?)"""
    cur.execute(sql, (lat_db,lon_db))
    sql="""INSERT INTO feature_Point(d) VALUES(?)"""
    cur.execute(sql, ([d_list]))
    sql="""INSERT INTO feature_Point(img) VALUES(?)"""
    cur.execute(sql, [gray_list])
    sql="""INSERT INTO feature_Point(name) VALUES(?)"""
    cur.execute(sql, [name])
    conn.commit()
    return cur,Num

def compare_img(img,Num,cur):
  #<特徴点抽出>
  sname=img+'.sift'
  process_image(img,sname)
  l1,d1 = read_features_from_file(sname) 
  #print 'Image',im_grey
  #print 'size',d1.ndim
  # print '\n'
  # <EXIF情報の取得>
  # もしEXIFがなければ０を返す
  try:
    GPS=get_exif(img)
    lat,lon=calculate(GPS)
  except AttributeError:
    lat=0
    lon=0
  cur.execute( "select * from feature_Point" )
  Num_list=['0','1','2','3','4','5','6','7','8','9']
  list_img=[]
  for i in range(4*Num): 
    start=time.time() 
    data_db=cur.fetchone()
    for k in range(5):
      df=data_db[k]
      if df != None:
        list_img.append(df)
    if len(list_img)==5:
      list_name=[]
      name_fin=str( )
      for n in range(len(list_img[4])):
        if n>8:
          df_n=str(list_img[4][n])
          name_fin=name_fin+df_n
      list_name.append(name_fin)
      print 'TEST',list_name
      list_Pre=[]
      list_inf=[]
      N_fin=str(0)
      for j in range(len(list_img[2])):
        N=str(list_img[2][j])
        # print N
        for k in Num_list:
          if N==k:
            N_fin=N_fin+N
            #print N_fin
        if N==',':
          list_Pre.append(int(N_fin))
          N_fin=str(0)
        if N==']':
          list_Pre.append(int(N_fin))          
        if len(list_Pre)==128:
          list_inf.append(list_Pre)
          list_Pre=[]
      list_inf=np.array(list_inf)
      # creation for return img
      list_ret=[]
      list_ret_Pre=[]
      df_ret=str(0)
      for k in range(len(list_img[3])):
        img_df=str(list_img[3][k])
        for l in Num_list:
          if img_df==l:
            df_ret=df_ret+img_df
        if img_df==' ':
            list_ret_Pre.append(int(df_ret))
            df_ret=str(0)
        if img_df==']':
          if len(list_ret_Pre)>1:
            list_ret.append(list_ret_Pre)
            list_ret_Pre=[]
      print 'RETURN',list_ret
      if lat>0 and lon>0:
        if abs(lat-list_img[0])<0.5 and abs(lon-list_img[1])<0.5:
          print 'OK'
          d_db=list_inf
          #入力画像とフィルタ通過したデータベース画像の特徴点マッチング開始
          matches = match(d1,d_db)
          #共通特徴点数の閾値
          if sum(matches)>50:
            nbr_matches = sum(matches > 0)
            print 'number of matches = ', nbr_matches
            #matchscores[i,j] = nbr_matches
            # print 'imagename:{0}'.format(img_ex)
            #次のプロセス画像としてリターンされる画像のRGB
            return lat,lon,list_name[0],list_inf
          else:
            print 'not mutch'
        elapsed_time = time.time() - start
        list_img=[]
        print ("elapsed_time:{0}".format(elapsed_time)) + "[sec]"
      if lat ==0 and lon==0:
        lat=list_img[0]
        lon=list_img[1]
        print 'No_GPS'
        d_db=list_inf
        #入力画像とフィルタ通過したデータベース画像の特徴点マッチング開始
        matches = match(d1,d_db)
        #共通特徴点数の閾値
        if sum(matches)>50:
          nbr_matches = sum(matches > 0)
          print 'number of matches = ', nbr_matches
          #matchscores[i,j] = nbr_matches
          # print 'imagename:{0}'.format(img_ex)
          #次のプロセス画像としてリターンされる画像のRGB
          return lat,lon,list_name[0],list_inf
        else:
          print 'not mutch'
      elapsed_time = time.time() - start
      list_img=[]
      print ("elapsed_time:{0}".format(elapsed_time)) + "[sec]"


#ここがメイン
#
#cur,Num=create_DB()
# img == input image
#img='KandaMyoujin.jpg'
#lat,lon,name,inf=compare_img(img,Num,cur)
