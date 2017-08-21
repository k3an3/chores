#!/usr/bin/env python3
# coding=utf-8
import json
import random
import time
from typing import Dict, List

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from utils import config, reload_config, safe_append, merge_chores, colors, update, should_run_bi_weekly, \
    should_run_quad_weekly

# Base URL for Slack incoming webhooks
SLACK_URL = 'https://hooks.slack.com/services/{}'


def get_quote_of_the_day() -> None:
    """
    Fetch a memorable quote and post it to Slack
    :return:
    """
    r = requests.get('http://quotes.rest/qod.json?category=inspire').json()
    quote = r['contents']['quotes'][0]
    data = {
        'text': '_"' + quote['quote'] + '" —' + quote['author'] + "_"
    }
    post_to_slack(data)


def post_to_slack(data: Dict) -> None:
    """
    Handle the request to Slack
    :param data: JSON-ready data
    """
    requests.post(SLACK_URL.format(config['slack_token']), data=json.dumps(data))


def chores_to_slack(name: str, user_chores: Dict) -> None:
    """
    Format the prepared user chores for Slack
    :param name: Name of these chores (weekly, bi-weekly, etc.)
    :param user_chores: Dictionary of each user and their assigned chores
    """
    for user in user_chores:
        data = {
            'text': '{} chores for <@{}>'.format(name, user),
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


def get_shared_chores(chores: Dict, chore_group: List) -> List:
    """
    Find chores that are shared and should be assigned to a pool of several users.
    :param chores: All chores
    :param chore_group: List of the categories that should be shared
    :return: A randomized list of chores to be assigned
    """
    shared_chores = []
    for group in chores:
        if group in chore_group:
            for chore in chores[group]:
                shared_chores.append((chore, group))
    return random.sample(shared_chores, len(shared_chores))


def get_user_chores(chores: Dict[str, str]) -> Dict[str, str]:
    """
    The meat of the program. Gets and assigns all the chores as desired.
    :param chores: All chores to assign
    :return: A dictionary of each user and their assigned chores
    """
    user_chores = {}
    # Prepare each user
    for user in config['users']:
        user_chores[user['name']] = {}
    # Randomly assign chores between all users
    for i, chore in enumerate(get_shared_chores(chores, config['shared_categories'])):
        safe_append(user_chores[config['users'][i % len(config['users'])]['name']], chore[1], chore[0])
    # Randomly assign chores between a secondary set of users
    for i, chore in enumerate(get_shared_chores(chores, config['secondary_shared_categories'])):
        safe_append(user_chores[config['secondary_shared_users'][i % len(config['secondary_shared_users'])]], chore[1],
                    chore[0])
    for group in chores:
        # We've already assigned the shared chores- move on
        if group in config['shared_categories']:
            pass
        # Whoever's not in the shared group has these chores on their own,
        # e.g. a second bathroom that's not shared
        elif group in config['secondary_shared_categories']:
            for user in config['users']:
                if user['name'] not in config['secondary_shared_users']:
                    for chore in chores[group]:
                        safe_append(user_chores[user['name']], group, chore)
        else:
            # Chores that need to go to every user individually
            for user in config['users']:
                for chore in chores[group]:
                    safe_append(user_chores[user['name']], group, chore)
    return user_chores


def get_chores(period: str) -> Dict[str, str]:
    """
    Find chores for this time period.
    :param period:
    :return: Dictionary of chores for this time period.
    """
    chores_dict = {}
    for group in config[period]:
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
    """
    Calculate whether any users have outstanding dues to pay the head of household, post to Slack.
    """
    for user in config['users']:
        if user.get('credit') and user['credit'] - config['dues'] <= 0:
            data = {
                'text': "<@{}>, you currently don't have enough credit"
                        " for the next rent payment. Please pay the minimum"
                        " amount to <@{}> as soon as possible. {}".format(user['name'], config['payto'],
                                                                          config.get('payments', ''))
            }
            post_to_slack(data)


def run_chores():
    """
    Decide which chores should be run, format them, and post to Slack.
    """
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

    print(get_user_chores(get_chores('weekly')))
    raise SystemExit

    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(update, trigger='cron', hour=6)
    sched.add_job(reload_config, trigger='cron', hour=7)
    sched.add_job(get_quote_of_the_day, trigger='cron', day_of_week='sat', hour=8)
    sched.add_job(run_chores, trigger='cron', day_of_week='sat', hour=8)
    sched.add_job(credit_check, trigger='cron', day='27-31', hour=8)

    while True:
        time.sleep(1)
