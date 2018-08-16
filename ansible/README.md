# Setup
```
virtualenv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

```
cp inventory_sample.yml inventory.yml
```
Edit `inventory.yml` so the host `chess-fracture` resolves to a CentOS 7 server (minimal installation)

# Client setup
visudo

```
ansible ALL=(ALL)       NOPASSWD:ALL
Defaults:ansible !requiretty
```

# Usage
```
ansible-playbook play.yml
```
