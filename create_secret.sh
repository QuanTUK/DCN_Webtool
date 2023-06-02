#!/bin/bash
key=$(python3 -c 'import secrets; print(secrets.token_hex())')

echo "SECRET_KEY = \"$key\"" > config.py
