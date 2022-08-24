from django.shortcuts import render,redirect,reverse
# from django.contrib.auth.models import User
from user.models import User
from django.contrib.auth import get_user_model
from celery_tasks.tasks import send_register_active_email
from django.views.generic import View
from authlib.jose import jwt,JoseError
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
import re

class RegisterView(View):
    """注册界面"""
    def get(self,request):
        return render(request, "register.html")

    """提交判断"""
    def post(self,request):

        #获取数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 数据校验
        if not all([username, password, cpassword, email]):
            return render(request, "register.html", {"errmsg": "数据不完整"})

        # 邮箱校验
        if not re.match(r"^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$", email):
            return render(request, "register.html", {"errmsg": "邮箱格式不正确"})

        # 协议勾选校验
        if allow != "on":
            return render(request, "register.html", {"errmsg": "未勾选协议"})

        # 两次密码是否满足简单要求校验
        if password != cpassword or len(password) < 8 or len(password) > 20:
            return render(request, "register.html", {"errmsg": "密码格式错误"})

        # 用户名校验
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, "register.html", {"errmsg": "用户名已存在"})

        # 数据业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 加密激活信息，发送用户信息，生成token，使用authlib
        info = {"confim":user.id}
        header = {'alg': 'HS256'}  # 签名算法
        token = jwt.encode(header=header,payload=info,key=settings.SECRET_KEY) #byte类型
        token = token.decode()

        # 给用户发邮件
        # subject = "天天生鲜注册信息" # 邮件标题
        # message = ""
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = '<h1>%s,欢迎成为天天生鲜注册会员<h1/><br/><a href="http://127.0.0.1:8000/user/active/%s">请点击以下链接来激活您的账户<br/>http://127.0.0.1:8000/user/active/%s<a/>'%(username,token,token)
        # send_mail(subject,message,sender,receiver,html_message=html_message)
        send_register_active_email.delay(email,username,token)

        # 返回应答
        return redirect(reverse("goods:index"))


class ActiveView(View):
    """获取用户激活信息"""
    def get(self,request,str):
        """解密获得用户信息"""
        try:
            info = jwt.decode(str,settings.SECRET_KEY)
            print(info)
            # 获取待激活用户的id
            user_id = info["confim"]

            # 根据id对用户进行激活
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录界面
            return redirect(reverse("user:login"))

        except JoseError:
            return HttpResponse("激活失败")


class LoginView(View):
    """登录界面"""
    def get(self,request):
        return render(request,"login.html")
