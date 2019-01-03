# TODO list
* https://github.com/wrouesnel/postgres_exporter
* sync only necessary files (roles/chessfracture-common/tasks/main.yml)
* errors: display gameid on error page, display gameid in logs (simulation failed)


# security
* limit max memory (systemd service)
* selinux
* passwords
  * grafana
  * postgres
* postgres 0.0.0.0/0
* django: https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/
* nginx
* uwsgi user
* listen socket 127.0.0.1
* rate limit (nginx)
