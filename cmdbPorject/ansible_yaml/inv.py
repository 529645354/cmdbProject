from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
import os
from collections import namedtuple
from cmdbPorject.settings import BASE_DIR
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase

hosts_path = os.path.join(BASE_DIR, "ansible_yaml/hosts")


class PlayBookCallBack(CallbackBase):
    CALLBACK_VERSION = 2.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_unreachable = {}
        self.task_failed = {}
        self.task_skipped = {}
        self.task_status = {}

    def v2_runner_on_unreachable(self, result):
        """
        重写 unreachable 状态
        :param result:  这是父类里面一个对象，这个对象可以获取执行任务信息
        """
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """
        重写 ok 状态
        :param result:
        """
        self.task_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        """
        重写 failed 状态
        :param result:
        """
        self.task_failed[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result):
        self.task_skipped[result._host.get_name()] = result


class InVenTory:
    def __init__(self):
        self.loader = DataLoader()
        self.inv = InventoryManager(loader=self.loader, sources=[hosts_path])
        self.var = VariableManager(loader=self.loader, inventory=self.inv)

    def add_group(self, group_name: list):
        for group in group_name:
            self.inv.add_group(group)

    def add_hosts(self, host_name: list):
        for hosts in host_name:
            self.inv.add_host(host=hosts.get("ipaddr"), group="all")
            self.inv.add_host(host=hosts.get("ipaddr"), group=hosts.get("group"))

    def inventory_content(self):
        print(self.inv.get_groups_dict())

    def Options(self, forks: int = 5, become: bool = None, become_user: str = None):
        Options = namedtuple('Options', [
            'connection',
            'module_path',
            'forks',
            'private_key_file',
            "become",
            "become_method",
            "become_user",
            'check',
            'diff',
            "listhosts",
            "listtasks",
            "listtags",
            "syntax",
            "remote_user"
        ])
        options = Options(connection='smart', module_path=None, become=become, become_method=None,
                          become_user=become_user,
                          check=False,
                          diff=False, forks=forks, remote_user="root",
                          listhosts=None, listtasks=None, listtags=None, syntax=None,
                          private_key_file=os.path.join(os.path.abspath("."), "id_rsa"))
        print(forks)
        return options

    def run_playbook(self, yaml: str, forks: int = 5, become: bool = None, become_user: str = None):
        play = PlaybookExecutor(playbooks=[os.path.join(BASE_DIR, "ansible_yaml/yml/" + yaml)],
                                inventory=self.inv, loader=self.loader,
                                options=self.Options(forks=forks, become=become, become_user=become_user),
                                passwords=dict(vault_pass='secret'), variable_manager=self.var)
        callback = PlayBookCallBack()
        play._tqm._stdout_callback = callback
        play.run()
        result_raw = {"ok": {}, "failed": {}, "unreachable": {}, "skipped": {}, "status": {}}
        for host, result in callback.task_ok.items():
            result_raw["ok"][host] = result._result

        for host, result in callback.task_failed.items():
            result_raw["failed"][host] = result._result

        for host, result in callback.task_unreachable.items():
            result_raw["unreachable"][host] = result._result

        for host, result in callback.task_skipped.items():
            result_raw["skipped"][host] = result._result
        return result_raw
