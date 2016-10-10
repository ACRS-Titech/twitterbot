# -*- coding:utf-8 -*-
import os
import sys
from PIL import Image
import numpy as np
import cv2
from matplotlib import pylab as plt
import sqlite3
from PIL.ExifTags import TAGS, GPSTAGS


def process_image(imagename,resultname,params="--edge-thresh 10 --peak-thresh 5"):
  """ 画像を処理してファイルに結果を保存する """

  if imagename[-3:] != 'pgm':
    # pgmファイルを作成する
    im = Image.open(imagename).convert('L')
    im.save('tmp.pgm')
    imagename = 'tmp.pgm'

  cmmd = str("./sift "+imagename+" --output="+resultname+ " "+params)
  os.system(cmmd)
  print 'processed', imagename, 'to', resultname

def read_features_from_file(filename):

  f = np.loadtxt(filename)
  return f[:,:4],f[:,4:]

# Plese explain this 'match' function 
def match(desc1,desc2):
  desc1 = np.array([d/np.linalg.norm(d) for d in desc1])
  desc2 = np.array([d/np.linalg.norm(d) for d in desc2])

  dist_ratio = 0.6 #なんで、0.6なのか？？？
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

#はじめにデータベース作成を行う
#<データベース作成　by sqlite3 > すみません・・・ここわからない
# shinohara データベース作成は先にやっておくべきでは？？？？
# このプログラム内でやる必要性がわからない
# つまり、ここから↓
conn = sqlite3.connect('ACRS.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE feature_Point(ID text,lat text,lon text,l text,d text,img text);""")

#データベース用のマッチングする画像(jpg)を保存したフォルダ Data_Box
#DataBox内のimgの名前、検出した特徴点情報，Exifのlat,lon,jpgのRGB情報をテーブルに格納（未完成）
path = 'Data_Box'
imlist = [os.path.join(path,f) for f in os.listdir(path) if f.endswith('.jpg')]
# 次のプロセスに渡す画像を入れるリスト

list_Img=[]
# データベース格納のための特徴点、GPS情報の算出
Num=0
for img_ex in imlist:
  Num=Num+1
  RGB=np.array(Image.open(img_ex))
  sname = img_ex+'.sift'
  process_image(img_ex,sname)
  l_db,d_db = read_features_from_file(sname) 
  GPS_db=get_exif(img_ex)
  lat_db,lon_db=calculate(GPS_db)
  print 'Data',lat_db,lon_db
  #データベースへ格納するため、stringへ変換
  Num=str(Num)
  RGB_str=str(RGB)
  lat_db_str=str(lat_db)
  lon_db_str=str(lon_db)
  l_db_str=str(l_db)
  d_db_str=str(d_db)
  #データベースへ格納
  sql="""INSERT INTO feature_Point(ID) VALUES(?)"""
  conn.execute(sql, Num)
  sql="""INSERT INTO feature_Point(lat,lon) VALUES(?,?)"""
  conn.execute(sql, (lat_db_str,lon_db_str))
  sql="""INSERT INTO feature_Point(l) VALUES(?)"""
  conn.execute(sql, [l_db_str])
  sql="""INSERT INTO feature_Point(d) VALUES(?)"""
  conn.execute(sql, [d_db_str])
  sql="""INSERT INTO feature_Point(img) VALUES(?)"""
  conn.execute(sql, [RGB_str])
  # sql="""INSERT INTO feature_Point(ID,lat,lon,l,d,img) VALUES(?,?,?,?,?,?)"""
  # conn.execute(sql, (Num,lat_db_str,lon_db_str,[l_db_str],[d_db_str],[RGB_str]))
  conn.commit()

# ここまで↑は別の関数にして、データベースだけを呼び出すようにしたい

#ここからを関数化するべき
# つまり、
#def DBmatching (画像のパスを引数):
# 入力画像
img='KandaMyoujin.jpg'#これが引数で渡される shinohara
# img_Num=np.array(Image.open(img))
# img_New=np.zeros((len(img_Num[:,0]),(len(img_Num[0,:]))))
#Gray_Scale process
# for i in range(len(img_Num[:,0])):
#   for j in range(len(img_Num[0,:])):
#     img_New[i,j]=int(round(0.299*img_Num[i,j][0]+0.587*img_Num[i,j][1]+0.114*img_Num[i,j][2]))
# img_gray = Image.fromarray(np.uint8(img_New))
#img_gray.show()

#<特徴点抽出>
sname=img+'.sift'
process_image(img,sname)
l1,d1 = read_features_from_file(sname) 
# print 'Sift',l1
# print d1
# print '\n'

# <EXIF情報の取得>
GPS=get_exif(img)
lat,lon=calculate(GPS)
print lat,lon
#本来ならば・・・データベースからGPS情報を呼び出して以下のif文(現時点では適当)でフィルタ
cur.execute( "select * from feature_Point" )
list_inf=[]
for row in cur: # rowはtuple
  for i in range(4):
    df=row[i]
    if df != None:
      list_inf.append(df)
print list_inf
  # if abs(lat-list_inf[1])<0.5 and abs(lon-list_inf[2])<0.5:
  # 	print 'OK'
  #   #本来ならば・・・フィルタ通過した画像の特徴点情報をデータベースから呼び出し
  #   #入力画像とフィルタ通過したデータベース画像の特徴点マッチング開始
  #   matches = match(d1,d_db)
  #   #共通特徴点数の閾値
  #   if sum(matches)>50:
  #     nbr_matches = sum(matches > 0)
  #     print 'number of matches = ', nbr_matches
  #     #matchscores[i,j] = nbr_matches
  #     print 'imagename:{0}'.format(img_ex)
  #     #次のプロセス画像としてリターンされる画像のRGB
  #     list_Img.append(RGB)
  #   else:
  #     print 'not mutch'

#さいご 次の関数にわたされる情報をreturn
# return hoge





