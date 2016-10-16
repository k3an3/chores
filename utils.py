import subprocess

import yaml

chores = {}


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
