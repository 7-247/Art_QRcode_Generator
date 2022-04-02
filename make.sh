#! /bin/bash
gunicorn -c gunicorn.py run:app
