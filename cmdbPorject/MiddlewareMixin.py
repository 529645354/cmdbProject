from django.utils.deprecation import MiddlewareMixin
import time


class Md1(MiddlewareMixin):
    def process_request(self, request):
        print("md1 request")

    def process_view(self, request, func, args, kwargs):
        print(args, kwargs)
        if request.path != '/index':
            print("tiaoguo")
            return None
        print("tiaoguo")
        start = time.time()
        response = func(request, *args, **kwargs)
        c = time.time() - start
        print(c)
        return response

    def process_response(self, request, response):
        print("md1 response")
        return response


class Md2(MiddlewareMixin):
    def process_request(self, request):
        print("md2 request")

    def process_response(self, request, response):
        print("md2 response")
        return response

    def process_view(self, request, func, *args, **kwargs):
        if request.path != '/index':
            print("tiaoguo")
            return None
        start = time.time()
        response = func(request)
        c = time.time() - start
        print(c)
        return response
