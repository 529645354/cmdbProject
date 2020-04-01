from django.views import View
from django.http import JsonResponse
from sqlutils import db
import IPy
import json
from status.status import Status


class QueryServer(View):
    def get(self, request):
        try:
            res = db.Query("select id,name,ipaddr from server")
        except Exception:
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"content": res})

    def post(self, request):
        try:
            res = json.loads(request.body.decode("utf8"))
        except json.decoder.JSONDecodeError:
            return JsonResponse({"status":Status.JsonDecodeError})
        hostName = res.get("name")
        hostIp = res.get("ip")
        hostSshUser = res.get("sshuser")
        hostSshPasswd = res.get("sshpasswd")
        if hostName == "" or hostIp == "" or hostSshUser == "" or hostSshPasswd == "":
            return JsonResponse({"status": Status.NotNone})
        try:
            IPy.IP(hostIp)
        except ValueError:
            return JsonResponse({"status": Status.ipError})

        try:
            db.Modify("insert into server(name,sshuser,sshpassword,ipaddr) values (%s,%s,%s,%s)",
                      [hostName, hostSshUser, hostSshPasswd, hostIp])
        except Exception:
            return JsonResponse({"status": Status.dbError})
        print(hostName, hostIp, hostSshPasswd, hostSshUser)
        return JsonResponse({"status": Status.Ok})

    def delete(self, request):
        content = request.body.decode("utf8")
        id = (json.loads(content)).get("id")
        try:
            db.Modify("delete from server where id=%s", [id])
        except Exception:
            return JsonResponse({"status": Status.dbError})
        return JsonResponse({"status": Status.Ok})
