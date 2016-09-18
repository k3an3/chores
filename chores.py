#!/usr/bin/env python3
import datetime
import json
import random
import sys
import time

import requests
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

SLACK_URL = 'https://hooks.slack.com/services/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'
DEV_URL = 'https://hooks.slack.com/services/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'
USERS = ('gemanley', 'jpbush', 'keane',)
SHARED_CATEGORIES = ('Kitchen', 'General',)
SECONDARY_SHARED_CATEGORIES = ('Bathroom',)
SECONDARY_SHARED_USERS = ('keane', 'gemanley',)

# SLACK_URL = DEV_URL

chores = {}


def get_week():
    return datetime.datetime.now().isocalendar()[1]


def should_run_bi_weekly():
    return get_week() % 2 == 1


def should_run_quad_weekly():
    return get_week() % 4 == 1


def get_quote_of_the_day():
    r = requests.get('http://quotes.rest/qod.json?category=inspire').json()
    quote = r['contents']['quotes'][0]
    data = {
        'text': '_"' + quote['quote'] + '" —' + quote['author'] + "_"
    }
    handle_post_to_slack(data)


def handle_post_to_slack(data):
    requests.post(SLACK_URL, data=json.dumps(data))


def post_to_slack(name, user_chores):
    get_quote_of_the_day()
    for user in user_chores:
        data = {
            'text': '{} chores for @{}'.format(name, user),
            'attachments': [],
        }
        for chore in user_chores[user]:
            data['attachments'].append({
                'fields': [
                    {
                        'title': chore.split(':')[0],
                        'value': chore.split(':')[1],
                        'short': 'false'
                    }
                ],
                'attachment_type': 'default',
                'actions': [
                    {
                        'name': 'done',
                        'text': 'Done',
                        'type': 'button',
                        'value': 'done',
                    },
                ],
            })
        handle_post_to_slack(data)


def get_user_chores(chores):
    user_chores = {}
    for user in USERS:
        user_chores[user] = []
    for group in chores:
        if group in SHARED_CATEGORIES:
            for chore in chores[group]:
                user_chores[random.choice(USERS)].append(group + ':' + chore)
        elif group in SECONDARY_SHARED_CATEGORIES:
            for chore in chores[group]:
                user_chores[random.choice(SECONDARY_SHARED_USERS)].append(
                    group + ':' + chore)
        else:
            for user in USERS:
                for chore in chores[group][1:]:
                    user_chores[user].append(group + ':' + chore)
    return user_chores


def get_chores(period):
    chores_dict = {}
    for group in chores[period]:
        chores_dict.update(group)
    return chores_dict


def bi_weekly_clean():
    if should_run_bi_weekly():
        post_to_slack('Bi-weekly', get_user_chores(get_chores('bi-weekly')))


def quad_weekly_clean():
    if should_run_quad_weekly():
        post_to_slack('Quad-weekly', get_user_chores(get_chores('quad-weekly')))


def weekly_clean():
    post_to_slack('Weekly', get_user_chores(get_chores('weekly')))


if __name__ == '__main__':
    f = open('chores.yml')
    chores.update(yaml.load(f))

    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(bi_weekly_clean, trigger='cron', day='6', hour='8')
    sched.add_job(weekly_clean, trigger='cron', day='6', hour='8')
    sched.add_job(quad_weekly_clean, trigger='cron', day='6', hour='8')

    x = 0
    while True:
        time.sleep(1)
        x += 1
        if x % 5 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
