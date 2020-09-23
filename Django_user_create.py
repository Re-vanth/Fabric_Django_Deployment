from fabric import Connection

from invoke import Responder

import sys

#host_name=sys.argv[1]


admin_user = Connection(host='<private-ip/hostname of remote machine',user='revanth') #admin user

application_user_name= Connection(host='<private-ip/hostname of remote machine',user='<application-user-name>') #application user name


sudo_pass= Responder(pattern=r'\[sudo\] password for revanth:', response='<admin-user-pass>\n') #admin user password

application_user_pass= Responder(pattern=r'Password', response='<application-user-pass>\n') #application user password




application_group= '<application-user-group>'

application_user= '<application-user-name>'





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
        admin_user.run('echo -e "<application-user-pass>\n<application-user-pass>" |sudo passwd {}'.format(application_user),pty=True, watchers=[sudo_pass])


def check_application_user_homedir():
    check_home_dir= admin_user.run('grep {} /etc/passwd | cut -d ":" -f6'.format(application_user))
    if '/'+application_user in check_home_dir.stdout.strip():
        admin_user.run('echo "the {} user already has a home directory"'.format(application_user))
    else:
        admin_user.run('sudo mkdir -p /home/{}/'.format(application_user), pty=True, watchers=[sudo_pass])
        admin_user.run('echo "created a home directory for the {} user"'.format(application_user))
        admin_user.run('sudo chown {}'.format(application_user)+' /home/{}/'.format(application_user), pty=True, watchers=[sudo_pass])






def application_user_creation():
    update_packages()
    admin_user.run('echo "********* UPDATING PACKAGES COMPLETE ********"')
    check_application_group()
    admin_user.run('echo "********* CHECKING APPLICATION GROUP COMPLETE ********"')
    check_application_user()
    admin_user.run('echo "********* CHECKING APPLICATION USER COMPLETE ********"')
    check_application_user_homedir()
    admin_user.run('echo "********* CHECKING APPLICATION USER HOME DIRECTORY COMPLETE ********"')



application_user_creation()




