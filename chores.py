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
USERS = ('gemanley', 'jpbush', 'keane',)
SHARED_CATEGORIES = ('Kitchen', 'General')

chores = {}

def get_week():
    return datetime.datetime.now().isocalendar()[1]


def should_run_bi_weekly():
    return get_week() % 2 == 1


def should_run_quad_weekly():
    return get_week() % 4 == 1


def post_to_slack(name, message):
    requests.post(SLACK_URL, data=json.dumps(parse_for_slack(name, message)))


def parse_for_slack(name, user_chores):
    for user in user_chores:
        data = {
           'text': '{} chores for @{}'.format(name, user),
            'attachments': [],
        }
        for chore in user_chores[user]:
            data['attachments'].append({
                'title': chore,
                'attachment_type': 'default',
                'actions':  [
                    {
                        'name': 'done',
                        'text': 'Done',
                        'type': 'button',
                        'value': 'done',
                    },
                ],
            })
        post_to_slack(data)


def get_user_chores(chores):
    user_chores = {}
    for user in USERS:
        user_chores[user] = []
    for group in chores:
        if group not in SHARED_CATEGORIES:
            for user in USERS:
                user_chores[user] += chores[group]
        else:
            for chore in chores[group]:
                user_chores[random.choice(USERS)].append(chore)
    return user_chores


def get_chores(period):
    chores_dict = {}
    for group in chores[period]:
        chores_dict.update(group)
    return chores_dict


def bi_weekly_clean():
    if should_run_bi_weekly():
        post_to_slack('Bi-weekly', get_user_chores(get_chores('bi-weekly')))


def weekly_clean():
    post_to_slack('Weekly', get_user_chores(get_chores('weekly')))


if __name__ == '__main__':
    f = open('chores.yml')
    chores.update(yaml.load(f))

    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(bi_weekly_clean, trigger='cron', day='6')
    sched.add_job(weekly_clean, trigger='cron', day='6')
    x = 0
    while True:
        time.sleep(1)
        x += 1
        if x % 5 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
