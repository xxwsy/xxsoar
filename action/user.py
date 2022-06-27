#!coding=utf-8
from tornadoweb import *
from core import *

@url(r"/login", needcheck = False, category = "用户")
class Login(BaseHandler):
    """
        用户登陆

        username*: 用户名
        password*: 密码
    """

    def get(self):
        self.post()

    def post(self):
        try:
            data = self.request.body.decode()
            username = json.loads(data).get("username")
            password = json.loads(data).get("password")
        except:
            username = self.get_argument("username")
            password = self.get_argument("password")

        if not username or not password:
            self.write(dict(status = False, msg = "用户名密码不能为空"))
            return

        MongoIns().m_update("user", dict(username = username), password = password_md5(password), upsert = True)
        user = MongoIns().m_find_one("user", username = username, password = password_md5(password))
        if user:
            self.set_secure_cookie("__UID__", user.get("_id"), expires_days = __conf__.COOKIE_EXPIRES_DAYS)
            self.write(dict(status = True, msg = "登陆成功", token = user.get("token")))
        else:
            self.write(dict(status = False, msg = "登陆失败"))


@url(r"/logout", needcheck = False, category = "用户")
class Logout(BaseHandler):
    """
        用户登出
    """
    def get(self):
        self.clear_cookie("__UID__")

        self.write(dict(status = True, msg="登出成功"))



@url(r"/token/gen", needcheck = False, category = "用户")
class UserTokenGen(LoginedRequestHandler):
    """
        Token生成

        response: {"status": True, "apikey": "token"}
    """

    def get(self):
        token = password_md5(str(uuid.uuid1()))
        MongoIns().m_update("user", {"_id": self.uid}, token = token)
        self.write(dict(status = True, token = token))

