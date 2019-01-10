#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from lxml import html
import requests
import chess.pgn
import urllib3
urllib3.disable_warnings()


PGN_FILE_PATH = '~/Downloads/lichess_tatrefthekiller_2019-01-10.pgn'


def get_csrf_token(s):
    try:
        r = s.get('https://chessfracture.net/chessfracture/')
        page = html.fromstring(r.text)
        csrf_token = page.xpath('//input[@name="csrfmiddlewaretoken"]/@value')[0]

        return csrf_token
    except Exception as e:
        raise Exception("Can't get csrf token " + str(e))


def submit_game(s, game_url):
    print('Submitting ' + game_url + '...')

    data = {
            'csrfmiddlewaretoken': get_csrf_token(s),
            'url': game_url,
            }

    r = s.post('https://chessfracture.net/chessfracture/fracture', data=data)
    if not r.ok:
        print('POST FAILED')
        print(game_url)
        print(r)
        sys.exit(1)


if __name__ == '__main__':
    s = requests.Session()
    s.verify = False

    try:
        pgn_file = sys.argv[1]
    except:
        print('Usage: ' + sys.argv[0] + ' /path/to/file.pgn')
        sys.exit(1)

    pgn = open(pgn_file)

    try:
        game = chess.pgn.read_game(pgn)
        i=1
    except Exception as e:
        pass
    while game:
       try:
           game = chess.pgn.read_game(pgn)
           if game.board().uci_variant != 'chess':
               continue
           game_url = game.headers['Site']
           submit_game(s, game_url)
           i += 1
           print(i)
           if i > 100:
               break
       except ValueError as e:
           pass

    print('DONE')

