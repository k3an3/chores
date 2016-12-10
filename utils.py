import subprocess

import yaml

chores = {}
colors = {
    'Kitchen': 'a37718',
    'Bathroom': '18a39e',
    'Living-room': 'a34418',
    'Bedroom': '1844a3',
    'General': '6318a3',
    'Personal': 'f47a42',
}


def update():
    subprocess.call(['git', 'pull', 'origin', 'master'])
    subprocess.call(['/srv/chores/env/bin/pip', 'install', '-r', 'requirements.txt', '--upgrade'])
    subprocess.call(['sudo', 'systemctl', 'restart', 'chores'])


def reload_config():
    chores.clear()
    with open('chores.yml') as f:
        chores.update(yaml.load(f))


def safe_append(target, key, chore):
    if not target.get(key):
        target[key] = []
    target[key].append(chore)


def merge_chores(user_chores):
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
