#!/bin/bash
source dcn_venv/bin/activate
cd DCN_Webtool
gunicorn views:app
