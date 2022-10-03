from django.shortcuts import render
from django.views.generic import View
from django.shortcuts import render,redirect,reverse
from goods.models import GoodsType,GoodsSKU,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection
from django.core.cache import cache
from django.shortcuts import render,redirect,reverse
from order.models import OrderGoods
from django.core.paginator import Paginator

# Create your views here.

class IndexView(View):
    """商品首页展示"""
    def get(self,request):
        """显示首页"""
        # 尝试从缓存中获取数据
        # cache.delete("index_page_data")
        context = cache.get("index_page_data")
        if context is None:
            # 获取商品种类信息
            types = GoodsType.objects.all()
            # 获取商品轮播信息
            goods_banners = IndexGoodsBanner.objects.all().order_by("index")
            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by("index")
            # 获取首页分类商品展示信息
            #print(types)
            for type in types:
                # 获取type种类首页分类商品图片的展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
                # 获取type种类首页分类商品文字的展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)
                # 获取商品种类的sku
                # skup = IndexTypeGoodsBanner.objects.get(type=type)

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息和商品种类sku
                type.image_banners = image_banners
                type.title_banners = title_banners
                # type.skup = skup
            print("缓存不存在，加载缓存")
            # 组织模板上下文
            context = {"types": types,
                       "goods_banners": goods_banners,
                       "promotion_banners": promotion_banners
                       }
            # 设置缓存 key value timout
            cache.set("index_page_data",context,3600)
        #
        # else:
        #     print("This is full")

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

        # return render(request, "index.html")



class DetailView(View):
    """详情页面"""
    def get(self,request,goods_id):

        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse("goods:index"))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取商品的评论
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment="")

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by("-create_time")[:2]

        # 获取同一个spu的其他规格信息
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)

        # 获取用户购物车商品的数目
        user = request.user
        # 默认为0
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户历史记录
            conn = get_redis_connection("default")
            history_key = "history_%d" % user.id
            # 移除表中的goods_id
            conn.lrem(history_key, 0, goods_id)
            # 把goods_id插入到列表的左端
            conn.lpush(history_key,goods_id)
            # 只保存用户最新浏览的5条信息
            conn.ltrim(history_key,0,4)

        # 组织模板上下文
        context = {"sku":sku,"types":types,
                   "sku_orders":sku_orders,
                   "new_skus":new_skus,
                   "same_spu_skus":same_spu_skus,
                   "cart_count":cart_count}

        # 使用模板


        return render(request,"detail.html",context)



class ListView(View):
    """列表页"""
    def get(self,request,type_id,page):
        # 获取type_id
        try:
            type = GoodsType.objects.get(id=type_id)
        except:
            return redirect(reverse("goods:index"))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取排序方式
        # sort = default 默认按id排序
        # sort = price 按price排序
        # sort = hot 按热度排序
        sort = request.GET.get("sort")
        if sort == "price":
            skus = GoodsSKU.objects.filter(type=type).order_by("price")
        elif sort == "hot":
            skus = GoodsSKU.objects.filter(type=type).order_by("-sales")
        else:
            sort = "default"
            skus = GoodsSKU.objects.filter(type=type).order_by("-id")

        # 对数据进行分页
        paginator = Paginator(skus,1)

        # 获取page页的内容
        try:
            page = int(page)
        except Exception:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的数据
        skus_page = paginator.page(page)

        # 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页 显示全部页码
        # 2.当前是前三页 显示1-5页
        # 3.后三页 显示后五页
        # 4.其他情况，显示当前页，和当前页前两页和后两页
        num_pages = paginator.num_pages
        if num_pages<5:
            pages = range(1,num_pages+1)
        elif page<=3:
            pages = range(1,6)
        elif num_pages-page<=2:
            pages = range(num_pages-4,num_pages+1)
        else:
            pages = range(page-2,page+3)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by("-create_time")[:2]

        # 获取用户购物车商品的数目
        user = request.user
        # 默认为0
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection("default")
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)

            # 组织模板上下文
            context = { 'type': type,'types':types,
                       'skus_page':skus_page,
                        'new_skus':new_skus,
                        'cart_count':cart_count,
                        'pages':pages,
                        'sort':sort}


        return render(request,"list.html",context)


