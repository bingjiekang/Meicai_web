from django.shortcuts import render,redirect,reverse
# from django.contrib.auth.models import User
from user.models import User
from django.contrib.auth import get_user_model

import re
# User = get_user_model()
# /user/register
def register(request):
    """注册"""
    if request.method == "GET":
        return render(request,"register.html")
    else:
        """进行数据处理"""
        # 接受数据
        # ''
        # username = request.POST.get('user_name')
        # password = request.POST.get('pwd')
        # cpassword = request.POST.get('cpwd')
        # email = request.POST.get('email')
        # allow = request.POST.get('allow')

        username = "xiaoming"
        password = "123456789"
        cpassword = "123456789"
        email = "123@qq.com"
        allow = "on"
        id = "0"
        last_login = 0
        is_superuser = "0"
        first_name = "xiao"
        last_name = "ming"
        is_staff = 1
        is_active = 0
        date_joined = 0
        create_time = 0
        update_time = 0
        is_delete = 0
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
        # user = User.objects.create_user(username, password, email)
        user = User()
        user.id = 2
        user.password = "123"
        user.last_login = 0
        user.is_superuser = 0
        user.username = "2"
        user.first_name = "xiao"
        user.last_name = "bai"
        user.email = "123@qq.com"
        user.is_staff = 1
        user.is_active = 1
        user.date_joined = 1
        user.create_time = 0
        user.update_time = 0
        user.is_delete = 0


        user.save()

        # user.is_active = 0
        # 返回应答
        return redirect(reverse("goods:index"))

# def register_handle(request):
#     """进行数据处理"""
#     # 接受数据
#     username = request.POST.get("user_name")
#     password = request.POST.get("pwd")
#     cpassword = request.POST.get("cpwd")
#     email = request.POST.get("email")
#     allow = request.POST.get("allow")
#
#     # 数据校验
#     if not all([username,password,cpassword,email]):
#         return render(request,"register.html",{"errmsg":"数据不完整"})
#     # 邮箱校验
#     if not re.match(r"^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$",email):
#         return render(request,"register.html",{"errmsg":"邮箱格式不正确"})
#     # 协议勾选校验
#     if allow!="on":
#         return render(request,"register.html",{"errmsg":"未勾选协议"})
#     # 两次密码是否满足简单要求校验
#     if password!=cpassword or len(password)<8 or len(password)>20:
#         return render(request,"register.html",{"errmsg":"密码格式错误"})
#
#     #用户名校验
#     try:
#         user = User.objects.get(username=username)
#     except User.DoesNotExist:
#         user = None
#     if user:
#         return render(request,"register.html",{"errmsg":"用户名已存在"})
#
#     # 数据业务处理
#     user = User.objects.create_user(username,password,email)
#     user.is_active = 0
#     user.save()
#     # 返回应答
#     return redirect(reverse("goods:index"))