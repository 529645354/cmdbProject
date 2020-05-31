from serverMon.ssh import SSH
from celery import Celery
import os
from docker_server.client_server import ServerRunDocker

celery = Celery('tasks', broker='redis://127.0.0.1:6379/0', backend='redis://127.0.0.1:6379/1')


@celery.task
def vnc(ip, ssh_user, ssh_pass_wd):
    m = SSH(hostname=ip, user=ssh_user, passwd=ssh_pass_wd)
    m.cmd("yum install -y tigervnc*")
    m.cmd("rm -rf /tmp/.X11-unix/*")
    m.cmd("rm -f /tmp/.X*-lock")
    m.cmd("rm -rf .vnc/")
    m.scp(os.path.join(os.path.abspath("."), "serverMon/websockify-master.tar.gz"), "/websockify.tar.gz")
    m.scp(os.path.join(os.path.abspath("."), "serverMon/vnc.tar.gz"), "vnc.tar.gz")
    m.cmd("tar zxf /websockify.tar.gz -C /")
    m.cmd("tar zxf vnc.tar.gz")
    m.cmd("vncserver :1")
    m.cmd("/websockify-master/websockify.py 6080 127.0.0.1:5901 &")
    return


@celery.task
def pullimage(image_name, addr):
    d = ServerRunDocker(addr)
    d.image_pull(image_name)
    return
