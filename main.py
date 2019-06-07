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

    app.run(debug=True, host='0.0.0.0', port=5000)