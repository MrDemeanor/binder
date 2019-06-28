#!/usr/bin/env bash
rm -R migrations
rm -rf app.db

flask db init
flask db migrate
flask db upgrade

python3 restore_user.py