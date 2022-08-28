from django.shortcuts import render,redirect,reverse
# from django.contrib.auth.models import User
from user.models import User,Address
from goods.models import GoodsSKU
from django.contrib.auth import get_user_model
from celery_tasks.tasks import send_register_active_email
from django.views.generic import View
from authlib.jose import jwt,JoseError
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
import re
from utils.Mixin import LoginRequiredMinin
from django_redis import get_redis_connection
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
        # 判断是否记住用户名
        if "username" in request.COOKIES:
            username = request.COOKIES.get("username")
            checked = "checked"
        else:
            username = ""
            checked = ""

        return render(request,"login.html",{"username":username,"checked":checked})

    def post(self,request):
        # 接收数据
        username = request.POST.get("username")
        password = request.POST.get("pwd")

        # 校验数据
        if not all([username,password]):
            return render(request,"login.html",{"errmsg":"数据不完整"})

        # 登录校验,处理数据
        user = authenticate(request,username=username, password=password)
        if user is not None:
            if user.is_active:
                # 记录用户登录状态
                login(request,user)

                # 获取申请跳转的界面
                # 默认跳转到首页
                next_url = request.GET.get("next",reverse("goods:index"))

                # 返回跳转的界面
                responce = redirect(next_url)

                # 判断用户是否需要记住用户名
                remmber = request.POST.get("remmber")

                if remmber=="on":
                    # 记住用户名
                    responce.set_cookie("username",username,7*24*3600)
                else:
                    # 删除cookie记住的用户名
                    responce.delete_cookie("username")
                return responce
            else:
                return render(request,"login.html",{"errmsg":"用户未激活"})
        else:
            return render(request,"login.html",{"errmsg":"用户不存在或者未激活或者密码不匹配"})


class LogoutView(View):
    """退出登录"""
    def get(self,request):
        # 注销用户
        logout(request)
        return redirect(reverse("goods:index"))




# /user/
class UserInfoView(LoginRequiredMinin, View):
    """用户中心-信息页"""
    def get(self,request):
        # 获取用户信息
        user = request.user
        address = Address.objects.get_default_address(user)
        # 获取用户最近浏览记录
        # 连接redis默认配置
        con = get_redis_connection("default")
        history_key = "history_%d"%user.id

        # 获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key,0,4)

        # 从数据库中查询商品id对应的信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        # 遍历获取用户查看的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        context = {"page":"user",
                   "address":address,
                   "goods_li":goods_li}

        # 返回信息页界面
        return render(request,"user_center_info.html",context)


# /user/order/
class UserOrderView(LoginRequiredMinin, View):
    """用户中心-订单页"""
    def get(self,request):
        # 显示用户订单

        # 返回订单页面
        return render(request,"user_center_order.html",{"page":"order"})


# user/Address
class AddressView(LoginRequiredMinin, View):
    """用户中心-地址页"""
    def get(self,request):
        # 获取用户默认收货界面
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)
        # 返回地址页面
        return render(request,"user_center_site.html",{"page":"address","address":address})

    def post(self,request):
        # 接收数据
        receiver = request.POST.get("receiver")
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")
        # 数据校验
        if not all([receiver,addr,phone]):
            return render(request,"user_center_site.html",{"errmsg":"数据不完整，请补全信息"})
        # 校验手机号
        if not re.match(r"^1[3|4|5|7|8][0-9]{9}$",phone):
            return render(request,"user_center_site.html",{"errmsg":"手机格式不正确"})
        # 数据处理，业务处理，地址添加
        # 如果有默认收货地址就显示默认收货地址，没有就添加地址显示
        user = request.user
        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答
        return redirect(reverse("user:address"))