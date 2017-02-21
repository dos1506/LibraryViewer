import falcon
import json
import requests
import xmltodict
from Steam import App

def InitializeSession():
  from sqlalchemy.orm import sessionmaker
  from sqlalchemy import create_engine
  
  Session = sessionmaker()
  engine = create_engine('mysql://python:R887EQwp@localhost/steam?charset=utf8mb4')
  Session.configure(bind=engine)
  session = Session()

  return session

def LoadAppList(session):
  applist = sorted(session.query(App).all(), key=lambda app: app.appid)
  return applist

class ProfileResource:

  def __init__(self):
    self.session = InitializeSession()
    self.applist = LoadAppList(self.session)

  def on_get(self, req, resp):
    try:
      steam_url = r'http://steamcommunity.com/'
      profile_url = req.get_param('profile', required=True)
      gamelist_xml = requests.get(steam_url + profile_url.strip('/') + '/games?xml=1').content
      gamelist = sorted(xmltodict.parse(gamelist_xml)['gamesList']['games']['game'],\
                        key=lambda game: int(game['appID']))
    except:
      resp.body = json.dumps({'error': 'profile not found'})
      return
  
    # {'gamesList': {'games': 'game': [...]}}
    i = 0
    for app in self.applist:
      if app.appid == int(gamelist[i]['appID']):
        gamelist[i]['tags'] = app.tags.split(';')
        i += 1

      if i >= len(gamelist):
        break


    resp.body = json.dumps(gamelist) 


app = falcon.API()
app.add_route('/steam/api', ProfileResource())

