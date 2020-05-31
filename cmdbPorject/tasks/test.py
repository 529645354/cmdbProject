from tasks.tk import vnc
# from celery.result import AsyncResult
#
# # task = vnc.apply_async(args=("192.168.119.130","root","redhat"))
# # print(task.id)
# print(AsyncResult(id="c4eef9fc-f576-4acb-8c20-b625262c1305").revoke(terminate=True))
# # print(str(AsyncResult(id="ea8e7716-a1e7-4835-a4b6-96e7c8b2fca6").result))
import requests, json
res = requests.get("https://index.docker.io/v1/search?q=mysql")
print(json.loads(res.content.decode("utf-8")).get("results"))
