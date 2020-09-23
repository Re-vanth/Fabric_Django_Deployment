from fabric import Connection

from invoke import Responder

import sys

#host_name=sys.argv[1]


admin_user = Connection(host='34.68.121.83',user='revanth')

application_user_name= Connection(host='34.68.121.83',user='itvadmin')


sudo_pass= Responder(pattern=r'\[sudo\] password for revanth:', response='revanth123\n')

application_user_pass= Responder(pattern=r'Password', response='itversity\n')




application_group= 'itversity'

application_user= 'itvadmin'


packages_list=['nginx','supervisor','postgresql',f'postgresql-contrib','lolcat','git',f'python3-venv']

postgresql_pass="'postgres'"

repo_name='workflow-test'



gunicorn_conf_file= '''[program:gunicorn]
directory=/home/itvadmin/sampleproject
command=/home/itvadmin/venv/bin/gunicorn --workers 3 --bind unix:/home/itvadmin/sampleproject/app.sock sampleproject.wsgi:application
autostart=true
autorestart=true
stderr_logfile=/home/itvadmin/sampleproject/sampleproject/log/gunicorn/gunicorn.err.log
stdout_logfile=/home/itvadmin/sampleproject/sampleproject/log/gunicorn/gunicorn.out.log
environment =
        DJANGO_SETTINGS_MODULE=sampleproject.settings

[group:guni]
programs:gunicorn
'''



nginx_conf_file= '''server {
    listen 80;
    server_name  104.155.172.90 ;

    location / {
    include proxy_params;
    proxy_pass http://unix:/itvadmin/sampleproject/app.sock;
    }

    location /static/{
    autoindex on;
    alias  /itvadmin/sampleproject/static/ ;
    }}
'''






def update_packages():
    admin_user.run('sudo apt -y update', pty=True, watchers=[sudo_pass])



def install_req_packages():
    for i in packages_list:
        
        install_package = admin_user.run("dpkg-query -W -f='${Status}\n'"+" {}".format(str(i)),warn=True)
        if 'install ok installed' in install_package.stdout.strip():
            admin_user.run('echo "package {} is already installed"'.format(str(i)))
        elif install_package.exited == 1 or 'unknown ok not-installed':
            admin_user.run('sudo apt install -y {}'.format(str(i)), pty=True, watchers=[sudo_pass])
            admin_user.run('echo "package {} is installed"'.format(str(i)))
            
            
            
            
            
def postgres_user():
    admin_user.run('sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD {} "'.format(postgresql_pass), pty=True, watchers=[sudo_pass])    


def create_app_db():
    admin_user.run ("PGPASSWORD='postgres' psql -U postgres -h localhost -c 'CREATE DATABASE app;'",warn=True)            


def git_pull():
    application_user_name.run('echo "pulling the latest code"')
    application_user_name.run('git pull origin master')

def git_init():
    application_user_name.run('git init')
    application_user_name.run('git remote add origin \'git@github.com:revanth-itv/workflow-test.git\'')
    application_user_name.run('git pull origin master')


def git_repo():
    git_check= application_user_name.run('ls -Fa | grep .git/',warn=True)
    repo_check= application_user_name.run('git config --get remote.origin.url',warn=True)
    if '.git/' in git_check.stdout.strip():
        if repo_name in repo_check.stdout.strip():
            git_pull()
    elif git_check.exited == 1:
        git_init()




def python_venv():
    application_user_name.run(f'/usr/bin/python3 -m venv venv\n')    



def install_req_pypkgs():
    application_user_name.run('venv/bin/pip install -r requirements.txt')    


def django_migrations():
    application_user_name.run(f'venv/bin/python sampleproject/manage.py migrate')
    application_user_name.run(f'venv/bin/python sampleproject/manage.py collectstatic --no-input')
    


def gunicorn_config():
    application_user_name.run(' mkdir -p sampleproject/sampleproject/log/gunicorn')    
    application_user_name.run('touch sampleproject/sampleproject/log/gunicorn/gunicorn.out.log sampleproject/sampleproject/log/gunicorn/gunicorn.err.log')

    gunicorn_conf=admin_user.run('cat /etc/supervisor/conf.d/gunicorn.conf', warn=True)

    if gunicorn_conf.exited == 1 :
        admin_user.run('echo "could not find a conf file for gunicorn so creating one at /etc/supervisor/conf.d/"')
        admin_user.run('echo "{}" >> /home/revanth/gunicorn.conf'.format(gunicorn_conf_file))
        admin_user.run('sudo mv /home/revanth/gunicorn.conf /etc/supervisor/conf.d/', pty=True, watchers=[sudo_pass])
    else:
        admin_user.run('echo "a conf file for gunicorn already exists"')




def supervisor_update():
    admin_user.run(f'sudo supervisorctl reread', pty=True, watchers=[sudo_pass]) 
    admin_user.run(f'sudo supervisorctl update', pty=True, watchers=[sudo_pass]) 
    admin_user.run(f'sudo supervisorctl status', pty=True, watchers=[sudo_pass])    


def nginx_config():
    nginx_conf=admin_user.run('cat /etc/nginx/sites-available/django.conf', warn=True)    
    if nginx_conf.exited == 1 :
        admin_user.run('echo "could not find a conf file for django so creating one at /etc/nginx/sites-available/"')
        admin_user.run('echo "{}" >> /home/revanth/django.conf'.format(nginx_conf_file))
        admin_user.run('sudo mv /home/revanth/django.conf /etc/nginx/sites-available/', pty=True, watchers=[sudo_pass])
        admin_user.run ('sudo ln /etc/nginx/sites-available/django.conf /etc/nginx/sites-enabled/',pty=True, watchers=[sudo_pass])
    else:
        admin_user.run('echo "a conf file for django already exists"')




def nginx_restart():
    admin_user.run(f'sudo service nginx restart', pty=True, watchers=[sudo_pass])    




def django_init_deployment():
    update_packages()
    admin_user.run('echo "********* UPDATING PACKAGES COMPLETE ********" ')
    install_req_packages()
    admin_user.run('echo "********* INSTALLING REQUIRED PACKAGES COMPLETE ********" ')
    postgres_user()
    admin_user.run('echo "********* POSTGRES USER SETUP COMPLETE ********" ')
    create_app_db()
    admin_user.run('echo "********* CREATING DATABASE FOR THE APPLICATION COMPLETE ********" ')
    git_repo()
    application_user_name.run('echo "********* REPOSITORY CLONE/PULL COMPLETE ********" ')
    python_venv()
    application_user_name.run('echo "********* CREATING PYTHON VENV COMPLETE ********" ')
    install_req_pypkgs()
    application_user_name.run('echo "********* INSTALLING REQUIRED PACKAGES FOR THE APPLICATION COMPLETE ********" ')
    django_migrations()
    application_user_name.run('echo "********* DJANGO MIGRATIONS COMPLETE ********" ')
    gunicorn_config()
    application_user_name.run('echo "********* GUNICORN CONFIGURATION COMPLETE ********" ')
    supervisor_update()
    application_user_name.run('echo "********* SUPERVISOR UPDATE COMPLETE ********" ')
    nginx_config()
    application_user_name.run('echo "********* NGINX CONFIGURATION COMPLETE ********" ')
    nginx_restart()
    application_user_name.run('echo "********* NGINX RESTART COMPLETE ********" ')




django_init_deployment()



