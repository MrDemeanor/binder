from app import app, db
from flask_login import current_user, login_user, logout_user
from app.models import UserModel, SemesterModel, ClassModel, OverrideModel
import os 
import threading
import schedule
import time
import requests
from bs4 import BeautifulSoup
import json

@app.shell_context_processor
def make_shell_context():
    """
        Allows for user to query and manipulate database in an interactive terminal session. 
    """
    return {    'db': db, 
                'UserModel': UserModel, 
                'SemesterModel': SemesterModel, 
                'ClassModel': ClassModel, 
                'OverrideModel': OverrideModel, 
                'current_user': current_user, 
                'login_user': login_user, 
                'logout_user': logout_user
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)