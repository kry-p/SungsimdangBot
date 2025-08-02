#!/bin/bash
REPOSITORY=../
VENV_PATH=../.venv

# Activate python venv 
python -m venv $VENV_PATH
. $VENV_PATH/bin/activate

# Install requirements
pip install -r  $REPOSITORY/requirements.txt

# Restart PM2
pm2 restart $REPOSITORY/bin/main.py --interpreter $VENV_PATH/bin/python