import datetime
import smtplib
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict

import yaml

config = {}
# Define sidebar colors for each section in Slack.
colors = {
    'Kitchen': 'a37718',
    'Bathroom': '18a39e',
    'Living-room': 'a34418',
    'Bedroom': '1844a3',
    'General': '6318a3',
    'Personal': 'f47a42',
}


def update():
    """
    Update from git
    """
    subprocess.call(['git', 'pull', 'origin', 'master'])
    subprocess.call(['/srv/chores/env/bin/pip', 'install', '-r', 'requirements.txt', '--upgrade'])
    subprocess.call(['sudo', 'systemctl', 'restart', 'chores'])


def reload_config() -> None:
    """
    Reload the config file.
    """
    config.clear()
    try:
        with open('chores.yml') as f:
            config.update(yaml.load(f))
    except FileNotFoundError:
        print("`chores.yml` not found! Copy `example-chores.yml` for a starting point.")


def safe_append(target: Dict, key: str, chore: Dict) -> None:
    """
    Simply make sure dictionary keys exist before adding to them
    :param target: Reference to dictionary
    :param key: The key to create or update
    :param chore: The chore to add to the dictionary
    """
    if not target.get(key):
        target[key] = []
    target[key].append(chore)


def merge_chores(user_chores: Dict) -> Dict:
    """
    Merge all chores into one mega dictionary.
    :param user_chores: The user chores
    :return: New dictionary
    """
    all_chores = {}
    for category in user_chores:
        for user in category:
            if not all_chores.get(user):
                all_chores[user] = {}
            for group in category[user]:
                if not all_chores[user].get(group):
                    all_chores[user][group] = []
                all_chores[user][group].extend(category[user][group])
    return all_chores


def get_week():
    return datetime.datetime.now().isocalendar()[1]


def should_run_bi_weekly():
    return get_week() % 2 == 1


def should_run_quad_weekly():
    return get_week() % 4 == 1


def email_users():
    for user in config['users']:
        if user.get('email'):
            yield user['name'], user['email']


def email_chores(email, message, chores):
    body = message + " chores:<br>"
    for cat in chores:
        body += "<br><b>" + cat + "</b><br>"
        for chore in chores[cat]:
            body += '<input type="checkbox"> ' + chore + "<br>"
    send_email(email, body)


# Adapted from http://stackoverflow.com/a/8321609/1974978
def send_email(email, data):
    msg = MIMEText(data, 'html')
    msg['Subject'] = "Chores"
    msg['To'] = email
    msg['From'] = config['mail_from']
    mail = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
    mail.starttls()
    mail.login(config['smtp_username'], config['smtp_password'])
    mail.sendmail(config['mail_from'], email, msg.as_string())
    mail.quit()
