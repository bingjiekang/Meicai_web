from django.contrib import admin
from django.urls import path,include
from order.views import OrderPlaceView,OrderCommitView,OrderPayView,CheckPayView
urlpatterns = [
    path("place/",OrderPlaceView.as_view(),name='place'),# 提交订单页面
    path("commit/",OrderCommitView.as_view(),name='commit'),# 提交订单界面
    path("pay/",OrderPayView.as_view(),name='pay'),# 支付界面返回
    path("check/",CheckPayView.as_view(),name='check'),# 完成界面返回
]
