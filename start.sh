#!/bin/bash
cd /srv/movies
/srv/movies/env/bin/gunicorn -b unix:///srv/movies/movies.sock main:app
