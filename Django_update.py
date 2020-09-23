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

repo_name='workflow-test'








def update_packages():
    admin_user.run('sudo apt -y update', pty=True, watchers=[sudo_pass])


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


def django_migrations():
    application_user_name.run(f'venv/bin/python sampleproject/manage.py migrate')
    application_user_name.run(f'venv/bin/python sampleproject/manage.py collectstatic --no-input')
    
    
def supervisor_update():
    admin_user.run(f'sudo supervisorctl reread', pty=True, watchers=[sudo_pass]) 
    admin_user.run(f'sudo supervisorctl update', pty=True, watchers=[sudo_pass]) 
    admin_user.run(f'sudo supervisorctl status', pty=True, watchers=[sudo_pass])    
    
    

def nginx_restart():
    admin_user.run(f'sudo service nginx restart', pty=True, watchers=[sudo_pass])    

    



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



django_update()
