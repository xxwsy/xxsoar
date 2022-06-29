#!coding=utf-8
import re
import os
import json
import uuid
import time
import base64
import jsonpath
from jsonpath_rw import jsonpath, parse
import threading
import multiprocessing
import requests
from hashlib import md5

from tornado import httpclient
from tornado import gen

from tornadoweb import *
from core import *


@url(r"/getMenuData", order = -1, needcheck = False, category = "PlayBook")
class GetMenuData(LoginedRequestHandler):
    """
        获取组件列表
    """
    def get(self):
        resp = requests.get("{}/functions".format(__conf__.FAAS_HOST), headers = HEADERS)
        functions = resp.json()
        func_map = {}
        for item in functions.values():
            for func in item.get("children"):
                func["icon"] = "el-icon-coin"
                func["disable"] = 0
                func_map[func["id"]] = func

        self.write(dict(status = True, result = list(functions.values()), func_map = func_map))

@url(r"/functions", order = -1, needcheck = False, category = "PlayBook")
class GetFunctions(LoginedRequestHandler):
    """
        获取函数
    """
    def get(self):
        resp = requests.get("{}/functions".format(__conf__.FAAS_HOST), headers = HEADERS)
        result = resp.json()
        functions = {}

        for item in result.values():
            for func in item.get("children"):
                functions[func["id"]] = dict(status = {"state": 1})

        self.write(functions)

@url(r"/function", order = -1, needcheck = False, category = "PlayBook")
class GetFunction(LoginedRequestHandler):
    """
        获取函数
    """
    def get(self):
        function = self.get_argument("function")
        resp = requests.get("{}/functions?function={}".format(__conf__.FAAS_HOST, function), headers = HEADERS)
        result = resp.json()
        function = list(result.values())[0]["children"][0]

        self.write(function)

    def post(self):
        function = self.get_argument("function")
        data = json.loads(self.request.body.decode())

        resp = requests.post("{}/functions?function={}".format(__conf__.FAAS_HOST, function), json=data, headers = HEADERS)
        ret = resp.json()

        os.system("supervisorctl -c supervisord.conf restart faas")
        self.write(ret)

@url(r"/playbook/upsert", order = -1, needcheck = False, category = "PlayBook")
@url(r"/playbook/save", order = -1, needcheck = False, category = "PlayBook")
class PlayBookSave(LoginedRequestHandler):
    """
        编排保存/编辑

        name:
        create_time:
        create_time:
        desc:
        playbook: json
    """
    async def post(self):
        data = json.loads(self.request.body.decode())
        _id = data.pop("id", None)
        name = data.pop("name", "")
        crontab = data.pop("crontab", "")
        desc = data.pop("desc", "")
        nodes = data.get("nodes")
        isroot = [item.get("isroot") for item in nodes if item.get("isroot") == 1]
        isend = [item.get("isend") for item in nodes if item.get("isend") == 1]
        if len(isroot) == 0:
            self.write(dict(status = False, msg = "请设置起始点"))
            return
        elif len(isroot) > 1:
            self.write(dict(status = False, msg = "设置了多个起始点"))
            return

        if len(isend) > 1:
            self.write(dict(status = False, msg = "设置了多个结束点"))
            return

        if not _id:
            _id = MongoIns().m_insert("playbook", playbook = data, name = name, crontab = crontab, desc = desc, uid = self.uid, create_time = time.time(), update_time = time.time())
        else:
            MongoIns().m_update("playbook", {"_id": ObjectId(_id)}, playbook = data, name = name, crontab = crontab, desc = desc, update_time = time.time(), upsert = True)

        self.write(dict(status = True, msg = "保存成功", playbook_id = _id))


@url(r"/playbook/del", order = -1, needcheck = False, category = "PlayBook")
class PlayBookDel(LoginedRequestHandler):
    """
        编排删除

        id: id
    """
    async def post(self):
        args = json.loads(self.request.body.decode())
        _id = args.get("id")
        _id = [ObjectId(_) for _ in _id]

        MongoIns().m_delete("playbook", _id = {"$in": _id})

        self.write(dict(status = True, msg = "删除成功"))

@url(r"/playbook/deploy", order = -1, needcheck = False, category = "PlayBook")
class PlayBookDeploy(LoginedRequestHandler):
    """
        编排部署

        id: id
        status: status
    """
    def post(self):
        args = json.loads(self.request.body.decode())

        _id = args.get("id")
        status = args.get("status") or 0

        playbook = MongoIns().m_find_one("playbook", _id = ObjectId(_id))
        if not playbook.get("crontab"):
            self.write(dict(status = False, msg = "请设置crontab表达式"))
            return

        MongoIns().m_update("playbook", {"_id": ObjectId(_id)}, status = status)

        self.write(dict(status = True, msg = "操作成功"))


@url(r"/playbook/get", order = -1, needcheck = False, category = "PlayBook")
class PlayBookGet(LoginedRequestHandler):
    """
        编排获取

        id: Objid
    """
    async def get(self):
        _id = self.get_argument("id")
        playbook = MongoIns().m_find_one("playbook", _id = ObjectId(_id))
        playbook["id"] = playbook.pop("_id")
        playbook["playbook"]["id"] = playbook["id"]

        self.write(dict(status = True, result = playbook))

@url(r"/playbook/status", order = -1, needcheck = False, category = "PlayBook")
class PlayBookStatus(LoginedRequestHandler):
    """
        编排获取

        id: Objid
    """
    async def get(self):
        _id = self.get_argument("_id")
        playbook = MongoIns().m_find_one("playbook", _id = ObjectId(_id))

        task_id = playbook.get("task_id")
        nodes = playbook['nodes']

        statusMap = {}
        if task_id:
            all_status = mq.hgetall(PLAYBOOK_TASK_NODE_STATUS.format(task_id))
            all_results = mq.hgetall(PLAYBOOK_TASK_NODE_RESULT.format(task_id))
            graphStatus = "success" if len(nodes) == len(all_status) and b"processing" not in all_status.values() else "processing"
            for node in nodes:
                node_id = node["id"]
                result = all_results.get(node_id.encode(), b'').decode()
                try:
                    result = json.loads(result)
                except:
                    pass

                statusMap[node_id] = {"status": all_status.get(node_id.encode(), b'default').decode(), "result": result}

        else:
            graphStatus = "processing"

        status = {
            "graphStatus": graphStatus,
            "statusMap": statusMap
        }


        self.write(status)


@url(r"/playbook", order = -1, needcheck = False, category = "PlayBook")
class PlayBook(LoginedRequestHandler):
    """
        编排保存/编辑
    """
    async def post(self):
        _id = self.args.pop("_id", None)

        if not _id:
            _id = MongoIns().m_insert("playbook", **self.args)
        else:
            MongoIns().m_update("playbook", {"_id": ObjectId(_id)}, **self.args)

        self.write(dict(status = True, msg = "保存成功", _id = _id))

    async def get(self):
        page_index = self.get_argument("current", 1)
        page_size = self.get_argument("pageSize", 10)

        data, page = MongoIns().m_list("playbook", page_index = page_index, page_size = page_size)

        self.write(dict(status = True, data = data, total = page.get("allcount")))

    def delete(self):
        _id = [ObjectId(_) for _ in self.args.pop("_id", [])]

        MongoIns().m_delete("playbook", _id = {"$in": _id})

        self.write(dict(status = True, msg = "删除成功"))

@url(r"/playbook/one", order = -1, needcheck = False, category = "PlayBook")
class PlayBookOne(LoginedRequestHandler):
    """
        playbook
    """
    async def get(self):
        _id = self.get_argument("_id", "")

        data = {"nodes": [], "edges": []}
        if _id:
            data = MongoIns().m_find_one("playbook", _id = ObjectId(_id))

        self.write(dict(status = True, data = data))


@url(r"/components", order = -1, needcheck = False, category = "PlayBook")
class ComponentsHandler(LoginedRequestHandler):
    """
        获取组件列表
    """
    def get(self):
        _projects = requests.get("{}/api/projects".format(__conf__.FAAS_HOST), headers = HEADERS)
        _projects = _projects.json()
        projects = {}
        for k, v in _projects.items():
            projects[k] = v["spec"]["description"]

        resp = requests.get("{}/api/functions".format(__conf__.FAAS_HOST), headers = HEADERS)

        functions = {}
        data = resp.json()

        for function_name, v in data.items():
            project_name = v["metadata"]["labels"]["nuclio.io/project-name"]
            project_name = projects.get(project_name) or project_name

            if project_name not in functions:
                functions[project_name] = {"id": project_name, "header": project_name, "children": []}

            code = v["spec"]["build"]["functionSourceCode"]
            code = base64.b64decode(code).decode()
            doc = code[code.index('"""')+3: code.rindex('"""')].strip().split("\r\n")
            label = doc[0]
            args = []
            for arg in doc[1:]:
                arg = arg.strip()
                args.append({"name": arg.split(":")[0], "label": arg.split(":")[1], "type": "text"})

            externalInvocationUrls = v["status"]["externalInvocationUrls"]
            functions[project_name]["children"].append({"label": label, "renderKey": "DND_NDOE", "function": function_name, "externalInvocationUrls": externalInvocationUrls, "args": args})

        default = functions.pop("default", None) or functions.pop("默认", None)
        if not default:
            self.write(dict(status = True, data = list(functions.values())))
        else:
            self.write(dict(status = True, data = [default] + list(functions.values())))
        return

        #resp = requests.get("{}/functions".format("http://127.0.0.1:8080"), headers = HEADERS)
        #functions = resp.json()
        #for item in functions.values():
        #    item["header"] = item.pop("label", None)
        #    for func in item["children"]:
        #        func["renderKey"] = "DND_NDOE"
        #        func["function"] = func.pop("id")


        #self.write(dict(status = True, data = list(functions.values())))

@url(r"/playbook/run", order = -1, needcheck = False, category = "PlayBook")
class PlayBookRun(LoginedRequestHandler):
    """
        编排运行

        id: Objid
    """
    def get(self):
        self.post()

    def post(self):
        _id = self.get_argument("_id", None) or self.args.get("_id")
        MongoIns().m_update("playbook", {"_id": ObjectId(_id)}, task_id = "")


        p = multiprocessing.Process(target=playbook_run, \
                args=(_id, self.request.headers.get("X-Forwarded-For") or self.request.remote_ip, ))
        p.daemon = True
        p.start()

        self.write(dict(status = True, msg = "任务启动"))
        return


@url(r"/node/id", order = -1, needcheck = False, category = "PlayBook")
class NodeID(LoginedRequestHandler):
    """
        获取id
    """
    def get(self):
        _id = self.get_argument("_id", None) or self.args.get("_id")
        i = mq.incr("PLAYBOOK_NODE_ID_{}".format(_id))

        self.write(dict(status = True, _id = str(i)))
        return

