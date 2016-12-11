#!/usr/bin/env python3
# coding=utf-8
import datetime
import json
import random
import time

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from utils import chores, reload_config, safe_append, merge_chores, colors

SLACK_URL = 'https://hooks.slack.com/services/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'
DEV_URL = 'https://hooks.slack.com/services/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'
USERS = ('gemanley', 'jpbush', 'keane',)
SHARED_CATEGORIES = ('Kitchen', 'General', 'Living-room')
SECONDARY_SHARED_CATEGORIES = ('Bathroom',)
SECONDARY_SHARED_USERS = ('keane', 'gemanley',)


# SLACK_URL = DEV_URL


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
    for user in user_chores:
        data = {
            'text': '{} chores for @{}'.format(name, user),
            'attachments': [],
        }
        for group in user_chores[user]:
            data['attachments'].append({
                'color': '#{}'.format(colors.get(group, '000000')),
                'fields': [
                    {
                        'title': group,
                        'value': '- ' + '\n- '.join(user_chores[user][group]),
                        'short': 'false',
                    },
                ],
            })
        post_to_slack(data)


def get_shared_chores(chores, chore_group):
    shared_chores = []
    for group in chores:
        if group in chore_group:
            for chore in chores[group]:
                shared_chores.append((chore, group))
    return random.sample(shared_chores, len(shared_chores))


def get_user_chores(chores):
    user_chores = {}
    for user in USERS:
        user_chores[user] = {}
    for i, chore in enumerate(get_shared_chores(chores, SHARED_CATEGORIES)):
        safe_append(user_chores[USERS[i % len(USERS)]], chore[1], chore[0])
    for i, chore in enumerate(get_shared_chores(chores, SECONDARY_SHARED_CATEGORIES)):
        safe_append(user_chores[SECONDARY_SHARED_USERS[i % len(SECONDARY_SHARED_USERS)]], chore[1], chore[0])
    for group in chores:
        if group in SHARED_CATEGORIES:
            pass
        elif group in SECONDARY_SHARED_CATEGORIES:
            for user in USERS:
                if user not in SECONDARY_SHARED_USERS:
                    for chore in chores[group]:
                        safe_append(user_chores[user], group, chore)
        else:
            for user in USERS:
                for chore in chores[group]:
                    safe_append(user_chores[user], group, chore)
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


def run_chores():
    all_chores = []
    chore_string = ""
    if should_run_quad_weekly():
        all_chores.append(get_user_chores(get_chores('quad-weekly')))
        chore_string += "Quad-Weekly, "
    if should_run_bi_weekly():
        all_chores.append(get_user_chores(get_chores('bi-weekly')))
        chore_string += "Bi-Weekly, "
    all_chores.append(get_user_chores(get_chores('weekly')))
    chore_string += "Weekly"
    all_chores = merge_chores(all_chores)
    chores_to_slack(chore_string, all_chores)


if __name__ == '__main__':
    reload_config()
    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(update, trigger='cron', hour=6)
    sched.add_job(reload_config, trigger='cron', hour=7)
    sched.add_job(get_quote_of_the_day, trigger='cron', day_of_week='sat', hour=8)
    sched.add_job(run_chores, trigger='cron', day_of_week='sat', hour=8)
    sched.add_job(credit_check, trigger='cron', day='27-31', hour=8)

    while True:
        time.sleep(1)
