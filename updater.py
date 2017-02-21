import Steam
import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

user = os.environ['USER_STEAM']
pswd = os.environ['PSWD_STEAM']
Session = sessionmaker()
engine = create_engine('mysql://{user}:{pswd}@localhost/steam?charset=utf8mb4'.format(user=user, pswd=pswd))
Session.configure(bind=engine)
session = Session()

Steam.UpdateAppDetails(session)

session.close()
