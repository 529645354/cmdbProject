import paramiko
import socket


class UserOrPassError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ConnTimeOut(UserOrPassError):
    pass


class ConnError(UserOrPassError):
    pass


class SSH:
    def __init__(self, hostname: str, user: str, passwd: str, port: int = 22):
        self.hostname = hostname
        self.user = user
        self.passwd = passwd
        self.port = port
        self.transport, self.sshObj = self.init_conn()

    def init_conn(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostname=self.hostname, port=self.port, password=self.passwd, username=self.user,
                        timeout=3)
        except paramiko.ssh_exception.AuthenticationException:
            raise UserOrPassError("账号或密码错误")
        except socket.timeout:
            raise ConnTimeOut("连接超时")

        try:
            transport = paramiko.Transport((self.hostname, self.port))
        except paramiko.ssh_exception.SSHException:
            raise ConnError("无法连接该地址")
        transport.connect(username=self.user, password=self.passwd)
        return transport, ssh

    def cmd(self, command):
        stdin, stdout, stderr = self.sshObj.exec_command(command)
        return stdin, stdout, stderr

    def scp(self, file: str, remotpath: str):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(file, remotpath)

    def send_authkey(self, key_path):
        self.scp(key_path, '.ssh/authorized_keys')

    def ssh_conn_close(self):
        self.sshObj.close()
        self.transport.close()


