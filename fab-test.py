from fabric import Connection

from invoke import Responder

import sys

#host_name=sys.argv[1]



admin_user = Connection(host='35.193.50.184',user='revanth')

application_user_name= Connection(host='35.193.50.184',user='itvadmin')


sudo_pass= Responder(pattern=r'\[sudo\] password for revanth:', response='revanth123\n')

application_user_pass= Responder(pattern=r'Password', response='itversity\n')




application_group= 'itversity'

application_user= 'itvadmin'




packages_list=['nginx','supervisor','postgresql',f'postgresql-contrib','git',f'python3-venv']

postgresql_pass="'postgres'"

repo_name='Labs Official'

gunicorn_conf_file= '''[program:gunicorn]
directory=/home/itvadmin/app
command=/home/itvadmin/venv/bin/gunicorn --workers 3 --bind unix:/home/itvadmin/app/app.sock app.wsgi:application
autostart=true
autorestart=true
stderr_logfile=/home/itvadmin/app/app/log/gunicorn/gunicorn.err.log
stdout_logfile=/home/itvadmin/app/app/log/gunicorn/gunicorn.out.log
environment =
        DJANGO_SETTINGS_MODULE=app.settings.development

[group:guni]
programs:gunicorn
'''




nginx_conf_file= '''server {
    listen 80;
    server_name  35.184.77.233 ;

    location / {
    include proxy_params;
    proxy_pass http://unix:/home/itvadmin/app/app.sock;
    }

    location /static/{
    autoindex on;
    alias  /home/itvadmin/app/static/ ;
    }}
'''


project_path_managepy = 'app/manage.py'

gunicorn_log_directory= 'app/app/log/gunicorn'

gunicorn_out_log= 'app/app/log/gunicorn/gunicorn.out.log'

gunicorn_error_log= 'app/app/log/gunicorn/gunicorn.err.log'

gunicornconf_path = '/etc/supervisor/conf.d/gunicorn.conf'

nginx_conf_path= '/etc/nginx/sites-available/django.conf'

git_repo_link= 'git@bitbucket.org:itversity-team/labs-official.git'




env_vars={"SECRET_KEY": os.environ.get('SECRET_KEY')}

'''
"DJANGO_SETTINGS_MODULE": os.environ.get('DJANGO_SETTINGS_MODULE'),
        "DJANGO_ALLOWED_HOSTS": os.environ.get('DJANGO_ALLOWED_HOSTS'),
        "SQL_ENGINE": os.environ.get('SQL_ENGINE'),
        "SQL_DATABASE": os.environ.get('SQL_DATABASE'),
        "SQL_USER": os.environ.get('SQL_USER'),
        "SQL_PASSWORD": os.environ.get('SQL_PASSWORD'),
        "SQL_HOST": os.environ.get('SQL_HOST'),
        "SQL_PORT": os.environ.get('SQL_PORT')
'''



def update_packages():
    admin_user.run('sudo apt -y update', pty=True, watchers=[sudo_pass])
    
    

def check_application_group():
    group_check= admin_user.run('getent group | cut -d: -f1')    
    if application_group in group_check.stdout.strip():       
        admin_user.run('echo "group {} exists"'.format(application_group))
    else:
        admin_user.run('sudo groupadd --system {}'.format(application_group), pty=True, watchers=[sudo_pass])



def check_application_user():
    application_user_check= admin_user.run('getent passwd | cut -d: -f1')

    if application_user in application_user_check.stdout.strip():
        admin_user.run('echo "user {} already exists"'.format(application_user))
    else:
        admin_user.run('sudo useradd --system --gid {0} -s /bin/bash -m -d /home/{1} {1}'.format(application_group,application_user),pty=True, watchers=[sudo_pass])
        admin_user.run('echo "created user {0} and assigned group {1}"'.format(application_user,application_group))
        admin_user.run('echo -e "itversity\nitversity" |sudo passwd {}'.format(application_user),pty=True, watchers=[sudo_pass])


def check_application_user_homedir():
    check_home_dir= admin_user.run('grep {} /etc/passwd | cut -d ":" -f6'.format(application_user))
    if '/'+application_user in check_home_dir.stdout.strip():
        admin_user.run('echo "the {} user already has a home directory"'.format(application_user))
    else:
        admin_user.run('sudo mkdir -p /home/{}/'.format(application_user), pty=True, watchers=[sudo_pass])
        admin_user.run('echo "created a home directory for the {} user"'.format(application_user))
        admin_user.run('sudo chown {}'.format(application_user)+' /home/{}/'.format(application_user), pty=True, watchers=[sudo_pass])




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
    create_db=admin_user.run ("PGPASSWORD='postgres' psql -U postgres -h localhost -c 'CREATE DATABASE app;'",warn=True)
    if create_db.exited == 1:
        admin_user.run('echo "The Database already Exists"')

def git_pull():
    application_user_name.run('echo "pulling the latest code"')
    application_user_name.run('git pull origin master')

def git_init():
    application_user_name.run('git init')
    application_user_name.run('git remote add origin \'{}\''.format(git_repo_link))
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
    application_user_name.run('/usr/bin/python3 -m venv venv\n')



def install_req_pypkgs():
    application_user_name.run('venv/bin/pip install -r requirements.txt')


def django_migrations():
    application_user_name.run('venv/bin/python {} migrate'.format(project_path_managepy))
    application_user_name.run('venv/bin/python {} collectstatic --no-input --settings=app.settings.base'.format(project_path_managepy))




def gunicorn_config():
    application_user_name.run(' mkdir -p {}'.format(gunicorn_log_directory))
    application_user_name.run('touch {0} {1}'.format(gunicorn_out_log,gunicorn_error_log))

    gunicorn_conf=admin_user.run('cat {}'.format(gunicornconf_path), warn=True)

    if gunicorn_conf.exited == 1 :
        admin_user.run('echo "could not find a conf file for gunicorn so creating one at /etc/supervisor/conf.d/"')
        admin_user.run('echo "{}" >> /home/admin/gunicorn.conf'.format(gunicorn_conf_file))
        admin_user.run('sudo mv /home/admin/gunicorn.conf /etc/supervisor/conf.d/', pty=True, watchers=[sudo_pass])
    else:
        admin_user.run('echo "a conf file for gunicorn already exists"')




def supervisor_update():
    admin_user.run(f'sudo supervisorctl reread', pty=True, watchers=[sudo_pass])
    admin_user.run(f'sudo supervisorctl update', pty=True, watchers=[sudo_pass])
    admin_user.run(f'sudo supervisorctl status', pty=True, watchers=[sudo_pass])


def nginx_config():
    nginx_conf=admin_user.run('cat {}'.format(nginx_conf_path), warn=True)
    if nginx_conf.exited == 1 :
        admin_user.run('echo "could not find a conf file for django so creating one at /etc/nginx/sites-available/"')
        admin_user.run('echo "{}" >> /home/admin/django.conf'.format(nginx_conf_file))
        admin_user.run('sudo mv /home/admin/django.conf /etc/nginx/sites-available/', pty=True, watchers=[sudo_pass])
        admin_user.run ('sudo ln /etc/nginx/sites-available/django.conf /etc/nginx/sites-enabled/',pty=True, watchers=[sudo_pass])
    else:
        admin_user.run('echo "a conf file for django already exists"')




def nginx_restart():
    admin_user.run(f'sudo service nginx restart', pty=True, watchers=[sudo_pass])






def application_user_creation():
    update_packages()
    admin_user.run('echo "********* UPDATING PACKAGES COMPLETE ********"')
    check_application_group()
    admin_user.run('echo "********* CHECKING APPLICATION GROUP COMPLETE ********"')
    check_application_user()
    admin_user.run('echo "********* CHECKING APPLICATION USER COMPLETE ********"')
    check_application_user_homedir()
    admin_user.run('echo "********* CHECKING APPLICATION USER HOME DIRECTORY COMPLETE ********"')




def django_init_deployment():
    update_packages()
    admin_user.run('echo "********* UPDATING PACKAGES COMPLETE ********" ')
    install_req_packages()
    admin_user.run('echo "********* INSTALLING REQUIRED PACKAGES COMPLETE ********" ')
    postgres_user()
    admin_user.run('echo "********* POSTGRES USER SETUP COMPLETE ********" ')
    create_app_db()
    admin_user.run('echo "********* CREATING DATABASE FOR THE APPLICATION COMPLETE ********" ')
    #git_repo()
    #application_user_name.run('echo "********* REPOSITORY CLONE/PULL COMPLETE ********" ')
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





def django_update():
    update_packages()
    admin_user.run('echo "********* UPDATING PACKAGES COMPLETE ********" | lolcat')
    git_repo()
    admin_user.run('echo "********* PULLING THE LATEST CODE IS COMPLETE ********" | lolcat')
    django_migrations()
    admin_user.run('echo "********* DJANGO MIGRATIONS COMPLETE ********" | lolcat')
    supervisor_update()
    admin_user.run('echo "********* SUPERVISOR UPDATE COMPLETE ********" | lolcat')
    nginx_restart()
    admin_user.run('echo "********* RESTART NGINX COMPLETE ********" | lolcat')





def env_var_test():
    admin_user.run('echo secret key is {}'.format(env_vars(0)))

