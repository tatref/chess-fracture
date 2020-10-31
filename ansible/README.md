# Server setup
```
virtualenv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

```
cp inventory_sample.yml inventory.yml
```
Edit `inventory.yml` so the host `chessfracture` resolves to a CentOS 7 server (minimal installation)

Generate the secret key

```
openssl rand 128 > ../django/mysite/secret_key
```

# Client setup
visudo

```
ansible ALL=(ALL)       NOPASSWD:ALL
Defaults:ansible !requiretty
```

```
ssh-copy-id ...
```

# PROD usage
```
ansible-playbook setup.yml -e firstcert=
```

# DEV usage
```
ansible-playbook setup.yml -e firstcert= -e dev=
```

## URLs
Main site
https://chessfracture.net

Prometheus
http://chessfracture.net:9090

Grafana
http://chessfracture.net:3000

