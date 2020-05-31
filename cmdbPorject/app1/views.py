from django.views import View
from django.http import JsonResponse
from sqlutils import db
import json
from status.status import Status
from django.conf import settings
import os
from serverMon.ssh import SSH, ConnTimeOut, UserOrPassError
from tasks.tk import vnc
from celery.result import AsyncResult


def check(ip):
    ip_split = ip.split(".")
    if len(ip_split) != 4:
        return False
    else:
        for i in ip_split:
            try:
                addr = int(i)
                if addr > 255:
                    return False
            except ValueError:
                return False
    return True


class QueryServer(View):
    # 查询所有主机
    def get(self, request):
        try:
            page = int(request.GET.get("page", 1))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        try:
            res = db.Query(
                "select id,name,ipaddr,(select name from cmdb.group where id=`group`) as `group` from server order by id desc limit %s,%s",
                [(page - 1) * 10, 10])
            count = db.Query("select count(id) from server")
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"content": res, "count": count[0].get('count(id)')})

    # 添加主机
    def post(self, request):
        try:
            res = json.loads(request.body.decode("utf8"))
        except json.decoder.JSONDecodeError:
            return JsonResponse({"status": Status.JsonDecodeError})
        host_name = res.get("name").strip()
        host_ip = res.get("ip").strip()
        host_ssh_user = res.get("sshuser").strip()
        host_ssh_password = res.get("sshpasswd").strip()
        if host_name == "" or host_ip == "" or host_ssh_user == "" or host_ssh_password == "":
            return JsonResponse({"status": Status.NotNone})
        if not check(host_ip):
            return JsonResponse({"status": Status.ipError})
        try:
            query_name = db.Query("select name from server where name = %s", [host_name])
            query_ip = db.Query("select ipaddr from server where ipaddr = %s", [host_ip])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        if len(query_name) != 0:
            return JsonResponse({"status": Status.nameIdentical})
        if len(query_ip) != 0:
            return JsonResponse({"status": Status.ipIdentical})

        try:
            m = SSH(hostname=host_ip, user=host_ssh_user, passwd=host_ssh_password)
        except ConnTimeOut as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except UserOrPassError as e:
            print(e)
            return JsonResponse({"status": Status.authError})

        try:
            m.send_authkey(os.path.join(settings.BASE_DIR, "serverMon/authorized_keys"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        m.ssh_conn_close()
        try:
            res = db.Modify("insert into server(name,sshuser,sshpassword,ipaddr) values (%s,%s,%s,%s)",
                            [host_name, host_ssh_user, host_ssh_password, host_ip])
            print(res)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})

    # 删除主机
    def delete(self, request):
        content = request.body.decode("utf-8")
        try:
            id = (json.loads(content)).get("id")
        except json.decoder.JSONDecodeError:
            return JsonResponse({"status": Status.JsonDecodeError})
        try:
            db.Modify("delete from server where id=%s", [id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})

    # 修改主机信息
    def put(self, request):
        try:
            res = json.loads(request.body.decode("utf8"))
        except json.decoder.JSONDecodeError:
            return JsonResponse({"status": Status.JsonDecodeError})
        try:
            id = int(res.get("id"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        host_name = res.get("name")
        host_ip = res.get("ip")
        host_ssh_user = res.get("sshuser")
        host_ssh_password = res.get("sshpasswd")
        print(id, host_name)
        if host_name == "" or host_ip == "" or host_ssh_user == "" or host_ssh_password == "":
            return JsonResponse({"status": Status.NotNone})
        if not check(host_ip):
            return JsonResponse({"status": Status.ipError})

        try:
            query_name = db.Query("select name from server where name = %s and id <> %s", [host_name, id])
            query_ip = db.Query("select ipaddr from server where ipaddr = %s and id <> %s", [host_ip, id])
            same_ip = db.Query("select ipaddr,sshuser,sshpassword from server where id = %s", [id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})

        if len(query_name) != 0:
            return JsonResponse({"status": Status.nameIdentical})
        if len(query_ip) != 0:
            return JsonResponse({"status": Status.ipIdentical})

        if same_ip[0].get("ipaddr") != host_ip or same_ip[0].get("sshuser") != host_ssh_user or same_ip[0].get(
                "sshpassword") != host_ssh_password:
            try:
                m = SSH(hostname=host_ip, user=host_ssh_user, passwd=host_ssh_password)
            except ConnTimeOut as e:
                print(e)
                return JsonResponse({"status": Status.timeOut})
            except UserOrPassError as e:
                print(e)
                return JsonResponse({"status": Status.authError})

            try:
                m.send_authkey(os.path.join(settings.BASE_DIR, "serverMon/authorized_keys"))
            except Exception as e:
                print(e)
                return JsonResponse({"status": Status.internalError})

        try:
            res = db.Modify("update server set name=%s,sshuser=%s,sshpassword=%s,ipaddr=%s where id=%s",
                            [host_name, host_ssh_user, host_ssh_password, host_ip, id])
            print(res)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})


class ServerGroup(View):
    # 查询所有组
    def get(self, request):
        try:
            page = int(request.GET.get("page", 1))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        try:
            res = db.Query("SELECT id,name FROM `group` order by id desc limit %s,%s", [(page - 1) * 10, 10])
            count = db.Query("select count(id) from `group`")
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"content": res, "count": count[0].get('count(id)')})

    # 添加组
    def post(self, request):
        res = request.body.decode("utf8")
        res = json.loads(res)
        group_name = res.get("name")
        if group_name.strip() == "":
            return JsonResponse({"status": Status.NotNone})
        try:
            group_name_query = db.Query("select name from `group` where name = %s", [group_name])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.nameIdentical})
        if len(group_name_query) != 0:
            return JsonResponse({"status": Status.nameIdentical})
        try:
            db.Modify("insert into `group`(name) value (%s)"
                      , [group_name])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})

    # 修改组名
    def put(self, request):
        try:
            res = json.loads(request.body.decode("utf8"))
        except json.decoder.JSONDecodeError:
            return JsonResponse({"status": Status.JsonDecodeError})
        group_name = res.get("name")
        id = res.get("id")
        if group_name.strip() == "" or not isinstance(id, int):
            return JsonResponse({"status": Status.NotNone})
        try:
            group_name_query = db.Query("select name from `group` where name = %s", [group_name])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.nameIdentical})
        if len(group_name_query) != 0:
            return JsonResponse({"status": Status.nameIdentical})
        try:
            db.Modify("update `group` set name=%s where id=%s", [group_name, id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})

    # 删除组
    def delete(self, request):
        res = request.body.decode("utf8")
        res = json.loads(res)
        id = res.get("id")
        if not isinstance(id, int):
            return JsonResponse({"status": Status.dataError})
        try:
            count = db.Query("select count(id) from server where `group`=%s", [id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        if count[0].get("count(id)") != 0:
            return JsonResponse({"status": Status.CannotDelete})
        try:
            db.Modify("delete from `group` where id=%s", [id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})


class ManageServer(View):
    def get(self, request):
        group_id = request.GET.get("id")
        try:
            res = db.Query("select id,name,ipaddr from server where server.group =  %s", [group_id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok, "content": res})

    def post(self, request):
        res = request.body.decode("utf8")
        try:
            res = json.loads(res)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.JsonDecodeError})
        group_id = res.get("group")
        server = res.get("server")
        try:
            for i in server:
                db.cour.execute("update  server set `group` = %s where id = %s", [group_id, i])
        except Exception as e:
            print(e)
            db.conn.rollback()
            return JsonResponse({"status": Status.dbError})
        else:
            db.conn.commit()
        return JsonResponse({"status": 200})

    def delete(self, request):
        req = request.body.decode("utf8")
        try:
            req = json.loads(req)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.JsonDecodeError})
        server_id = req.get("id")
        if not isinstance(server_id, int):
            return JsonResponse({"status": Status.dataError})
        try:
            db.Modify("update cmdb.server set `group` = null where id= %s", [server_id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})


def get_no_group_server(request):
    if request.method == "GET":
        try:
            res = db.Query("SELECT id,name FROM cmdb.server where `group` is null")
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": 200, "content": res})
    else:
        return JsonResponse({"status": 500, "content": "无效请求"})


def install_vnc(request):
    if request.method == "POST":
        res = request.body.decode("utf8")
        try:
            res = json.loads(res)
            print(res)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.JsonDecodeError})

        try:
            id = int(res.get("server"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})

        try:
            content = db.Query("select ipaddr,sshuser,sshpassword from server where id = %s", [id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})

        if len(content) == 0:
            return JsonResponse({"status": Status.dataNotExist})
        res = vnc.apply_async(args=(content[0].get("ipaddr"), content[0].get("sshuser"), content[0].get("sshpassword")))
        try:
            db.Modify("insert into tasks(task,task_id) values (%s,%s)",
                      ["对ip:%s安装vnc" % content[0].get("ipaddr"), res.id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})


def get_tasks(request):
    if request.method == "GET":
        tasks_list = []
        try:
            res = db.Query("select task,date_time,task_id from tasks order by id desc")
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        else:
            for i in res:
                t = AsyncResult(id=i["task_id"])
                if t.ready():
                    i["ready"] = 1
                    if t.successful():
                        i["success"] = 1
                        i["res"] = "成功执行"
                    else:
                        i["success"] = 0
                        i["res"] = str(t.result)
                else:
                    i["ready"] = 0
                    i["success"] = 0
                    i["res"] = "就绪中"
                tasks_list.append(i)
            return JsonResponse({"status": Status.Ok, "content": tasks_list})
    if request.method == "DELETE":
        res = request.body.decode("utf8")
        try:
            res = json.loads(res)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        task_id = res.get("tasks_id")
        print(task_id)
        try:
            AsyncResult(id=task_id).revoke(terminate=True)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        try:
            db.Modify("delete from tasks where task_id = %s", [task_id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})
