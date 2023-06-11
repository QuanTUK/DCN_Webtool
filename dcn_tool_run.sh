#!/bin/bash
source dcn_venv/bin/activate
cd DCN_Webtool
gunicorn --config 'gunicorn_conf.py' views:app
