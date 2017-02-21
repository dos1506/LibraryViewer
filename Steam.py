import requests
import os
import json
import re
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String,\
                       create_engine, MetaData, update
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup

base = declarative_base()

user = os.environ['USER_STEAM']
pswd = os.environ['PSWD_STEAM']
engine = create_engine('mysql://{user}:{pswd}@localhost/steam?charset=utf8mb4'.format(user=user, pswd=pswd)
base.metadata.create_all(bind=engine)

class App(base):
  __tablename__ = 'Apps'

  appid = Column(Integer, primary_key=True, autoincrement=False)
  name = Column(String)
  genre = Column(String)
  recent_review = Column(Integer)
  all_review = Column(Integer)
  recommendations = Column(Integer)
  tags = Column(String)

  def __str__(self):
    return ('<appid: {appid}, name: {name}, genre: {genre}, recent_review: {recent_review}, '\
           +'all_review: {all_review}, recommendations: {recommendations}, tags: {tags}>')\
            .format(appid=self.appid, name=self.name, genre=self.genre,\
                    recent_review=self.recent_review, all_review=self.all_review,\
                    recommendations=self.recommendations, tags=self.tags)


def UpdateAppList(session):
  applist_uri = 'http://api.steampowered.com/ISteamApps/GetAppList/v0001/'
  applist_raw = requests.get(applist_uri).text

  # applist_raw == {'applist': {'apps': {'app': [...]}}}
  applist = json.loads(applist_raw)['applist']['apps']['app']
  apps = list()
  for app in applist:
    record = session.query(App).filter(App.appid==int(app['appid'])).first()
    if record is None:
      apps.append(App(appid=int(app['appid']),
                  name=app['name'], 
                  genre=None,
                  recent_review=None, 
                  all_review=None, 
                  recommendations=None,
                  tags=None))

  # データベースの操作はできるだけ少なくしたい
  if apps: 
    session.add_all(apps)
    session.commit()


def UpdateAppDetails(session):
  appids = session.query(App.appid)
  
  for appid in appids:
    store_uri = 'http://store.steampowered.com/app/{}?l=english'.format(appid[0])
    
    # 年齢確認ページの回避用 Cookie
    cookie = dict(birthtime = '-473417999')
    store_html = requests.get(store_uri, cookies=cookie, allow_redirects=False).text

    print('appid: {} start'.format(appid[0]))
    record = session.query(App).filter(App.appid==int(appid[0])).first() 
    record.recent_review, record.all_review = ParseReviewRates(store_html)  
    record.recommendations = ParseReviewCount(store_html)
    record.tags = ';'.join(ParseTags(store_html))
    record.genre = GetGenre(record.appid)
    print('appid: {} complete'.format(record.appid))
  
  session.commit()


def ParseReviewRates(html):
  soup = BeautifulSoup(html, 'lxml')

  review_rate_class = 'span.nonresponsive_hidden.responsive_reviewdesc'
  review_info = soup.select(review_rate_class)

  pattern = r'\d{,3}%'
  review_rates = re.findall(pattern, str(review_info))
  
  if review_rates:
    recent_review_rate = int(review_rates[0].strip("'").replace('%', ''))
    all_review_rate = int(review_rates[-1].strip("'").replace('%', ''))
  else:
    recent_review_rate = None
    all_review_rate = None

  return recent_review_rate, all_review_rate


def ParseTags(html):
  soup = BeautifulSoup(html, 'lxml')
  
  tag_class = 'a.app_tag'
  tag_info = str(soup.select(tag_class))

  if tag_info:
    html_pattern = r'<.*>' 
    tag_info = re.sub(html_pattern, '', tag_info)
    pattern = r'[\w\ \-\']+'
    tags = re.findall(pattern, tag_info)
  else:
    tags = None

  return tags


def GetGenre(appid):
  appdetails_uri = 'http://store.steampowered.com/api/appdetails?appids={}'.format(appid)
  appdetail = json.loads(requests.get(appdetails_uri).text)

  if appdetail is None:
    return None

  if appdetail[str(appid)]['success'] is True:
    return appdetail[str(appid)]['data']['type']
  else:
    return None
   

def ParseReviewCount(html):
  soup = BeautifulSoup(html, 'lxml')
  
  review_count_class = 'span.responsive_hidden'
  recommendations = soup.select(review_count_class)

  if recommendations:
    recommendations = str(recommendations)
    pattern = r'[\,\d]+'
    recommendations = re.findall(pattern, recommendations)[-1]
    # カンマを削除して数値へ
    recommendations = int(recommendations.replace(',', ''))
    return recommendations
  else:
    return None
