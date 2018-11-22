# Single machine setup

Components:
* Postgres DB: contains the list of games, and simulations if already computed
* django app: a client connects to the web app, the web app inserts the new job into Postgres. When a job gets completed, django sends the simulation results back to the client
* nginx + uwsgi: reverse proxy in front of django
* workers: each worker connects to the DB, waiting for new jobs to be submited by django. Each worker can spin 1 blender process
* turbovnc: blender can't run properly without a GUI, turbovnc is used to provide it. You can watch blender working by connecting to turbovnc (requires SSH tunneling, because vnc is listening on 127.0.0.1)

# Multi machine setup

Same as previous, but the workers can be split on multiple machines. They need access to postgres though.
