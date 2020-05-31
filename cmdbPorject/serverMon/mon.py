import psutil
import datetime
import time


class Mon:
    @staticmethod
    def cpu():
        # cpu逻辑核心数
        cpu_count = psutil.cpu_count(logical=False)
        # cpu利用率
        cpu_use = psutil.cpu_percent(1)
        print(datetime.datetime.now().strftime('%H:%M:%S'))
        return {"cpu_use": cpu_use, "cpu_count": cpu_count, "time": str(datetime.datetime.now().time()).split('.')[0]}

    @staticmethod
    def disk():
        device = []
        disk_use = []
        disk_free = []
        for i in psutil.disk_partitions():
            p = psutil.disk_usage(i.mountpoint)
            device.append(i.device)
            disk_use.append("%.2f" % (int(p.used) / (1024 * 1024 * 1024)))
            disk_free.append("%.2f" % (int(p.free) / (1024 * 1024 * 1024)))
        return {"device_name": device, "disk_use": disk_use, "disk_free": disk_free}

    @staticmethod
    def inputnet():
        netl = []
        for i in psutil.net_io_counters(pernic=True).keys():
            rate = {"name": "", "rate": 0}
            r = psutil.net_io_counters(pernic=True).get(i).bytes_recv / 1024
            time.sleep(0.2)
            n = psutil.net_io_counters(pernic=True).get(i).bytes_recv / 1024
            rate["name"] = i
            rate["rate"] = "%.2f" % (n - r)
            netl.append(rate)
        psutil.disk_partitions()
        return {"net": netl, "time": str(datetime.datetime.now().time()).split('.')[0]}

    @staticmethod
    def net():
        netl = []
        for i in psutil.net_io_counters(pernic=True).keys():
            rate = {"name": "", "rate": 0}
            r = psutil.net_io_counters(pernic=True).get(i).bytes_sent / 1024
            time.sleep(0.2)
            n = psutil.net_io_counters(pernic=True).get(i).bytes_sent / 1024
            rate["name"] = i
            rate["rate"] = "%.2f" % (n - r)
            netl.append(rate)
        return {"net": netl, "time": str(datetime.datetime.now().time()).split('.')[0]}

    @staticmethod
    def mem():
        # 空闲内存
        free_mem = (psutil.virtual_memory().total - psutil.virtual_memory().used) / (1024 * 1024 * 1024)

        # 已用内存
        use_mem = psutil.virtual_memory().used / (1024 * 1024 * 1024)
        return {"use_mem": '%.2f' % use_mem, "free_mem": '%.2f' % free_mem}
