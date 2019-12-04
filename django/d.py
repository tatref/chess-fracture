#!/usr/bin/env python


import sys, os
import subprocess
import zipfile
import io
import time
import signal
import resource
import chess.pgn

import django
from django.db import transaction
from django import db
from django.utils import timezone
import requests


sys.path.append('/home/{}/chessfracture/django/mysite'.format(os.environ['USER']))
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()

from chessfracture.models import Game, Worker


import code
code.iteract(local=locals())


