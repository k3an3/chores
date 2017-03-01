# chores
Does my chores.

A quick-and-dirty python3 solution to distribute chores in a multi-person apartment using Slack's incoming webhooks.

## Installation
Set up an incoming webhook on Slack.

```
git clone https://github.com/keaneokelley/chores.git
cd chores
cp example-chores.yml chores.yml
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
# If using systemd
cp chores.service /etc/systemd/system # make sure to configure ExecStart/WorkingDirectory paths!
sudo systemctl start chores
# otherwise
python3 chores.py
```

You'll also need to give chores its own user and edit sudoers (`visudo`) if you want chores to be able to update itself and restart the service using systemctl:
```chores ALL=NOPASSWD: /bin/systemctl restart chores```
