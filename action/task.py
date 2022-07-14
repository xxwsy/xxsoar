#!coding=utf-8
import time
import json
from hashlib import md5

from core import *


@url(r"/task/list", category = "任务列表")
class TaskList(LoginedRequestHandler):
    """
        任务列表
    """
    def get(self):
        search = self.get_argument('search', None)
        playbook_id = self.get_argument('playbook_id', None)
        page_index = int(self.get_argument('current', 1))
        page_size = int(self.get_argument('pageSize', 10))

        sort = self.get_argument('sort', None)
        # 方向 desc
        direction = self.get_argument('direction', '')

        cond = {}
        if playbook_id:
            cond["playbook_id"] = playbook_id


        total = MongoIns().m_count("task", **cond)
        results, page = MongoIns().m_list("task", page_index = page_index, page_size = page_size, sorts = [("_id", -1)], **cond)

        for item in results:
            item.pop("pid")
            item["id"] = item.get("_id")
            playbook_id = item.get("playbook_id")
            playbook = MongoIns().m_find_one("playbook", _id = ObjectId(playbook_id))
            if playbook:
                item["playbook_name"] = playbook.get("name")

            if item.get("result"):
                item["simple_flag"] = 0
                item["cost_time"] = 1
                try:
                    _result = item["result"]
                    item["result_length"] = int(len(str(_result))/1024 * 100)/100
                    if item["result_length"] >= 256:
                        item["result"] = simplify_object(_result)
                        item["simple_flag"] = 1
                except:
                    pass

        self.write(dict(total = total, data = results))


from tornado import gen
@url(r"/task/stop", category = "任务列表")
class TaskStop(LoginedRequestHandler):
    """
        任务停止
    """
    @gen.coroutine
    def get(self):
        _id = self.get_argument("id")

        task = MongoIns().m_find_one("task", _id = _id)

        mq.set("PLAYBOOK-TASK-STATUS-{}".format(task.task_id), "STOP")

        yield gen.sleep(3)
        if task:
            os.system("kill {}".format(task.pid))

        print ("task stop wait 3 s")
        from playbook.playbook import get_task_status
        playbook = MongoIns().m_find_one("playbook", _id = task.playbook_id)

        result = ""
        if playbook:
            task_status, result = get_task_status(task.task_id, json.loads(playbook["playbook"])["nodes"])

        MongoIns().m_update("task", {"_id": _id}, status = 1, result = result, end_time = time.time())

        self.write(dict(status = True, msg = ""))


@url(r"/task/result", category = "任务结果")
class TaskResult(LoginedRequestHandler):
    """
        任务结果
    """
    def get(self):
        _id = self.get_argument('id')

        result = MongoIns().m_find_one("task", _id = _id)

        result.pop("pid")
        playbook_id = result.get("playbook_id")
        playbook = MongoIns().m_find_one("playbook", _id = playbook_id)
        if playbook:
            result["playbook_name"] = playbook.name

        if result.get("result"):
            try:
                result["result"] = json.loads(result["result"])
            except:
                pass

        self.write(dict(status = True, result = result.get("result")))


@url(r"/task/del", category = "任务结果")
class TaskResult(LoginedRequestHandler):
    """
        任务删除
    """
    def post(self):
        args = json.loads(self.request.body.decode())
        _id = [ObjectId(_) for _ in args.get("id")]

        MongoIns().m_delete("task", _id = {"$in": _id})

        self.write(dict(status = True))

