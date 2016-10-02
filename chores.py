#!/usr/bin/env python3
# coding=utf-8
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
SHARED_CATEGORIES = ('Kitchen', 'General', 'Living-room')
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
    post_to_slack(data)


def post_to_slack(data):
    requests.post(SLACK_URL, data=json.dumps(data))


def chores_to_slack(name, user_chores):
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
        post_to_slack(data)


def get_shared_chores(chores, chore_group):
    shared_chores = []
    for group in chores:
        if group in chore_group:
            for chore in chores[group]:
                shared_chores.append(group + ':' + chore)
    return random.sample(shared_chores, len(shared_chores))


def get_user_chores(chores):
    user_chores = {}
    for user in USERS:
        user_chores[user] = []
    for i, chore in enumerate(get_shared_chores(chores, SHARED_CATEGORIES)):
        print('shared-assigning chore', chore, 'to', USERS[i%len(USERS)])
        user_chores[USERS[i % len(USERS)]].append(chore)
    for i, chore in enumerate(get_shared_chores(chores, SECONDARY_SHARED_CATEGORIES)):
        print('secondary-shared-assigning chore', chore, 'to', SECONDARY_SHARED_USERS[i%len(SECONDARY_SHARED_USERS)])
        user_chores[SECONDARY_SHARED_USERS[i % len(SECONDARY_SHARED_USERS)]].append(chore)
    for group in chores:
        if group in SHARED_CATEGORIES:
            pass
        elif group in SECONDARY_SHARED_CATEGORIES:
            for user in USERS:
                if user not in SECONDARY_SHARED_USERS:
                    print('assigning chore', chore, 'to', user)
                    user_chores[user].append(
                        group + ':' + chore)
        else:
            for user in USERS:
                for chore in chores[group][1:]:
                    print('assigning chore', chore, 'to', user)
                    user_chores[user].append(group + ':' + chore)
    return user_chores


def get_chores(period):
    chores_dict = {}
    for group in chores[period]:
        chores_dict.update(group)
    return chores_dict


def bi_weekly_clean():
    if should_run_bi_weekly():
        chores_to_slack('Bi-weekly', get_user_chores(get_chores('bi-weekly')))


def quad_weekly_clean():
    if should_run_quad_weekly():
        chores_to_slack('Quad-weekly', get_user_chores(get_chores('quad-weekly')))


def weekly_clean():
    chores_to_slack('Weekly', get_user_chores(get_chores('weekly')))


def credit_check():
    for bill in chores['credit']:
        if bill['credit'] - chores['dues'] <= 0:
            data = {
                'text': "@{}, you currently don't have enough credit"
                " for the next rent payment. Please pay the minimum"
                " amount to Keane as soon as possible. goo.gl/BKUN3b".format(
                    bill['name']
                )
            }
            post_to_slack(data)


def reload_config():
    chores.clear()
    with open('chores.yml') as f:
        chores.update(yaml.load(f))


if __name__ == '__main__':
    reload_config()

    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(reload_config, trigger='cron', hour=7)
    sched.add_job(bi_weekly_clean, trigger='cron', day_of_week='sat', hour=8)
    sched.add_job(weekly_clean, trigger='cron', day_of_week='sat', hour=8)
    sched.add_job(quad_weekly_clean, trigger='cron', day_of_week='sat', hour=8)
    sched.add_job(credit_check, trigger='cron', day='27-31', hour=8)

    while True:
        time.sleep(1)