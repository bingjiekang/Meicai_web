from django.contrib import admin
from django.urls import path,include
from user.views import RegisterView,ActiveView,LoginView,UserInfoView\
    ,UserOrderView,AddressView,LogoutView

urlpatterns = [
    # path("register/", views.register,name="register"),#注册
    # path("register_handle/", views.register_handle,name="register_handle"),#注册处理
    path("register/",RegisterView.as_view(),name="register"),# 用户注册界面
    path("active/<str:str>/",ActiveView.as_view(),name="active"),# 用户激活界面
    path("login/",LoginView.as_view(),name="login"),# 用户登录界面
    path("",UserInfoView.as_view(),name="user"),# 用户的信息页面
    path("order/<int:page>/", UserOrderView.as_view(), name="order"),  # 用户的订单页面
    path("address/", AddressView.as_view(), name="address"),  # 用户的地址页面
    path("logout/",LogoutView.as_view(),name="logout"), # 用户退出登录

]
