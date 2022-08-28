from django.shortcuts import render
from django.views.generic import View
from django.shortcuts import render,redirect,reverse
from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection
from django.core.cache import cache
# Create your views here.

class IndexView(View):
    """商品首页展示"""
    def get(self,request):
        """显示首页"""
        # 尝试从缓存中获取数据
        context = cache.get("index_page_data")
        if context is None:
            # 获取商品种类信息
            types = GoodsType.objects.all()
            # 获取商品轮播信息
            goods_banners = IndexGoodsBanner.objects.all().order_by("index")
            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by("index")
            # 获取首页分类商品展示信息
            for type in types:
                # 获取type种类首页分类商品图片的展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
                # 获取type种类首页分类商品文字的展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners
            print("缓存不存在，加载缓存")
            # 组织模板上下文
            context = {"types": types,
                       "goods_banners": goods_banners,
                       "promotion_banners": promotion_banners
                       }
            # 设置缓存 key value timout
            cache.set("index_page_data",context,3600)



        # 获取用户购物车商品的数目
        user = request.user
        # 默认为0
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = "cart_%d"%user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context.update(cart_count=cart_count)

        return render(request,"index.html",context)
