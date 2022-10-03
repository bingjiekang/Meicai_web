from django.contrib import admin
from django.urls import path,include
from carts.views import CartAddView,CartInfoView,CartUpdateView,CartDeleteView
urlpatterns = [
    path("add/",CartAddView.as_view(),name='add'),# 购物车记录添加
    path("",CartInfoView.as_view(),name='cart'), # 购物车显示
    path("update/",CartUpdateView.as_view(),name='update'), #购物车更新
    path("delete/",CartDeleteView.as_view(),name='delete'), #购物车商品删除
]
