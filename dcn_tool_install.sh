#!/bin/bash
python3 -m venv dcn_venv
source dcn_venv/bin/activate
pip3 install -r requirements.txt

key=$(python3 -c 'import secrets; print(secrets.token_hex())')
echo "SECRET_KEY = \"$key\"" > config.py
