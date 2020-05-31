from django.views import View
from django.http import JsonResponse
from django.conf import settings
import os
import json
from status.status import Status
from sqlutils import db
from ansible_yaml.inv import InVenTory
import docker
from requests.exceptions import ConnectTimeout, ConnectionError
from docker.errors import DockerException, ImageNotFound
from docker_server.client_server import ServerRunDocker
from tasks.tk import pullimage
import requests


class yaml(View):
    def get(self, request):
        dl = []
        dir_list = os.listdir(os.path.join(settings.BASE_DIR, "ansible_yaml/yml"))
        for i in dir_list:
            if i.split(".")[1] == "yml" or i.split(".")[1] == "yaml":
                dl.append(dict(name=i))
        return JsonResponse({"status": 200, "content": dl})

    def post(self, request):
        obj = request.FILES.get("file")
        if obj.name.split(".")[-1] == "yaml" or obj.name.split(".")[-1] == "yml":
            if obj.name in os.listdir(os.path.join(settings.BASE_DIR, "ansible_yaml/yml")):
                return JsonResponse({"status": Status.nameIdentical})

            with open(os.path.join(settings.BASE_DIR, "ansible_yaml/yml/" + obj.name), "wb") as f:
                for c in obj.chunks():
                    f.write(c)
            return JsonResponse({"status": Status.Ok})
        else:
            return JsonResponse({"status": Status.dataError})

    def delete(self, request):
        content = request.body.decode("utf8")
        try:
            content = json.loads(content)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        name = content.get("name")
        os.remove(os.path.join(settings.BASE_DIR, "ansible_yaml/yml/" + name))
        return JsonResponse({"status": Status.Ok})


def get_group(request):
    if request.method == "GET":
        try:
            res = db.Query("select id, name from `group`")
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok, "content": res})


def run_ansible(request):
    if request.method == "POST":
        content = request.body.decode("utf-8")
        try:
            content = json.loads(content)
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        group_list = content.get("group")
        forks = content.get("forks")
        become = content.get("become")
        busers = content.get("busers")
        yname = content.get("yaml")
        hosts = []
        print(db.Query("select name from `group` where id=%s", [i])for i in group_list)
        gname = [db.Query("select name from `group` where id=%s", [i])[0].get("name") for i in group_list]
        for i in group_list:
            hosts += db.Query(
                "select ipaddr,(select name from `group` where id=%s) as `group` from server where `group` = %s",
                [i, i])
        ansi = InVenTory()
        ansi.add_group(gname)
        ansi.add_hosts(hosts)
        res = ansi.run_playbook(yname, forks=forks, become_user=busers, become=become)
        return JsonResponse({"stauts": Status.Ok, "content": {"ok": res["ok"],
                                                              "failed": res["failed"],
                                                              "unreachable": res["unreachable"],
                                                              "skip": res["skipped"]}})


class DockerServer(View):
    def get(self, request):
        try:
            res = db.Query("select id,name,ipaddr,port from docker_server")
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        else:
            return JsonResponse({"status": Status.Ok, "content": res})

    def post(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"statue": Status.dataError})
        name = content.get("name")
        ipaddr = content.get("ipaddr")
        port = content.get("port")
        print(content)
        if name == "" or ipaddr == "" or port == "":
            return JsonResponse({"status": Status.NotNone})
        try:
            exists_data = db.Query("select id from docker_server where name = %s or ipaddr = %s ", [name, ipaddr])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        if len(exists_data) != 0:
            return JsonResponse({"status": Status.dataExist})
        client = docker.DockerClient(base_url=ipaddr + ":" + port, timeout=3)
        try:
            client.ping()
            db.Modify("insert into docker_server (name,ipaddr,port) values (%s,%s,%s)", [name, ipaddr, port])
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        except DockerException as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})

    def delete(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        print(content)
        try:
            db.Modify("delete from docker_server where id = %s", [content.get("serverid")])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})


def ConnDockerServer(request):
    if request.method == "POST":
        try:
            res = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        id = res.get("id")
        print(id)
        try:
            con = db.Query("select ipaddr,port from docker_server where id = %s", [id])[0]
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        if len(con) == 0:
            return JsonResponse({"statue": Status.dataNotExist})
        ipaddr = con.get("ipaddr")
        port = con.get("port")
        uri = ipaddr + ":" + port
        try:
            d = ServerRunDocker(uri)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        else:
            return JsonResponse({"status": Status.Ok, "addr": ipaddr + ":" + port})


def search_image(request):
    if request.method == "POST":
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        image_name = content.get("image")
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
            "Cookie": "optimizelyEndUserId=oeu1589771869752r0.0432147948435726; _gcl_au=1.1.59239418.1589771870; _biz_uid=b755a41e881d41e1c8897818106b5cb7; _biz_nA=1; _mkto_trk=id:929-FJL-178&token:_mch-docker.io-1589771873142-35341; _biz_pendingA=%5B%5D",
            "Host": "index.docker.io",
            "Sec-Fetch-Mode": "navigate"
        }
        try:
            res = requests.get("https://index.docker.io/v1/search", timeout=60, headers=headers, params={"q": image_name})
        except requests.exceptions.ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except requests.exceptions.ReadTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        return JsonResponse({"status": Status.Ok, "content": json.loads(res.content.decode("utf-8")).get("results")})


class DockerGetImage(View):
    def get(self, request):
        remote_addr = request.GET.get("addr")
        print(remote_addr)
        try:
            d = ServerRunDocker(remote_addr)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        image = []
        for i in d.image_list():
            for name in i.tags:
                image.append(
                    {"name": name.split(":")[0], "tag": name.split(":")[1], "id": i.short_id.split(":")[1],
                     "port": list(i.attrs.get("ContainerConfig").get("ExposedPorts").keys()) if i.attrs.get(
                         "ContainerConfig").get("ExposedPorts") else None,
                     "size": "%d" % float(i.attrs.get("Size") / 1000 / 1000)}
                )
        return JsonResponse({"content": image})

    def delete(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        name = content.get("name")
        tag = content.get("tag")
        addr = content.get("addr")
        image = name + ":" + tag
        try:
            d = ServerRunDocker(addr)
            d.remove_image(image)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        except docker.errors.APIError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        return JsonResponse({"status": Status.Ok})

    def put(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        addr = content.get("addr")
        old_image_name = content.get("name")
        new_image_repo_name = content.get("repo")
        tag = content.get("tag")

        print(old_image_name, new_image_repo_name, tag)
        try:
            d = ServerRunDocker(addr)
            d.tag(image_name=old_image_name, reponame=new_image_repo_name, tag=tag)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        except ImageNotFound as e:
            print(e)
            return JsonResponse({"status": Status.dataExist})
        else:
            return JsonResponse({"status": Status.Ok})

    def post(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        image_name = content.get("image")
        ipaddr = content.get("addr")
        res = pullimage.apply_async(args=(image_name, ipaddr))
        try:
            db.Modify("insert into tasks(task,task_id) value(%s,%s)",
                      ["对" + ipaddr + "容器服务器pull镜像:" + image_name, res.id])
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})


class ContainerServer(View):
    def getea(self, hport):
        if hport.attrs.get("HostConfig").get("PortBindings"):
            return [h.get("HostPort") for d in hport.attrs.get("HostConfig").get("PortBindings").values() for h in d]
        else:
            return None

    def geted(self, dport):
        if dport.attrs.get("HostConfig").get("PortBindings"):
            return list(dport.attrs.get("HostConfig").get("PortBindings").keys())
        else:
            return None

    def get(self, request):
        addr = request.GET.get("addr")
        print(addr)
        try:
            d = ServerRunDocker(addr)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        res = [{"id": i.short_id, "name": i.attrs.get("Name").split("/")[-1],
                "status": i.status,
                "dport": self.geted(i),
                "networkmode": list(i.attrs.get("NetworkSettings").get("Networks").keys()),
                "image": i.attrs.get("Config").get("Image"),
                "hport": self.getea(i),
                "networkaddr": i.attrs.get("NetworkSettings").get("Networks").get("bridge").get("IPAddress")
                }
               for i in d.container_list()]
        return JsonResponse({"status": Status.Ok, "content": res})

    def delete(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        addr = content.get("addr")
        id = content.get("id")
        try:
            d = ServerRunDocker(addr)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        d.container_delete(id)
        return JsonResponse({"status": Status.Ok})

    def post(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        addr = content.get("addr")
        id = content.get("id")
        try:
            d = ServerRunDocker(addr)
            d.start_container(id)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        except docker.errors.APIError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        return JsonResponse({"status": Status.Ok})

    def put(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        addr = content.get("addr")
        container_id = content.get("id")
        try:
            d = ServerRunDocker(addr)
            d.container_kill(container_id)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        return JsonResponse({"status": Status.Ok})


class ContainerNetWork(View):
    def getsubnet(self, i):
        if i.attrs.get("IPAM").get("Config"):
            return i.attrs.get("IPAM").get("Config")[0].get("Subnet")
        else:
            return None

    def getgateway(self, i):
        if i.attrs.get("IPAM").get("Config"):
            return i.attrs.get("IPAM").get("Config")[0].get("Gateway")
        else:
            return None

    def get(self, request):
        try:
            d = ServerRunDocker(request.GET.get("addr"))
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        res = [{"id": i.short_id, "name": i.attrs.get("Name"), "mode": i.attrs.get("Driver"),
                "gateway": self.getgateway(i),
                "subnet": self.getsubnet(i)} for i in d.network_list()]
        return JsonResponse({"status": Status.Ok, "content": res})

    def delete(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        addr = content.get("addr")
        id = content.get("id")
        try:
            d = ServerRunDocker(addr)
            d.network_delete(id)
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        except docker.errors.APIError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        return JsonResponse({"status": Status.Ok})

    def post(self, request):
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"statamus": Status.dataError})
        if content.get("name") == None or content.get("subnet") == None or content.get("gateway") == None:
            return JsonResponse({"status": Status.NotNone})
        try:
            d = ServerRunDocker(content.get("addr"))
            d.network_create(name=content.get("name"), subnet=content.get("subnet"),
                             gateway=content.get("gateway"))
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        except docker.errors.APIError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        return JsonResponse({"status": Status.Ok})


def RunContainer(request):
    if request.method == "POST":
        try:
            content = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            print(e)
            return JsonResponse({"status": Status.dataError})
        print(content)
        port = content.get("port")
        volumes = content.get("volume")
        env = content.get("env")
        if content.get("name") == None or content.get("network") == None:
            return JsonResponse({"status": Status.NotNone})
        e = {}
        for i in env:
            e[i.get("key")] = i.get("value")
        v = {}
        for i in volumes:
            v[i.get("hvolume")] = {"bind": i.get("dvolume")}
        p = {}
        for i in port:
            p[i.get("dport")] = [h for h in i.get("hport").split(",")]
        try:
            d = ServerRunDocker(content.get("addr"))
            d.run_container(image=content.get("image"), command=content.get("command"), ports=p, env=e,
                            network_id=content.get("network"), name=content.get("name"))
        except ConnectTimeout as e:
            print(e)
            return JsonResponse({"status": Status.timeOut})
        except ConnectionError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
        except docker.errors.APIError as e:
            print(e)
            return JsonResponse({"status": Status.internalError})
    return JsonResponse({"status": Status.Ok})
