from django.shortcuts import render,redirect,reverse
from django.views.generic import View
from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo,OrderGoods
from django_redis import get_redis_connection
from utils.Mixin import LoginRequiredMinin
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime
from django.db import transaction
import time
from alipay import AliPay
from alipay.utils import AliPayConfig
# Create your views here.
# 订单页面
# /cart/place/
class OrderPlaceView(LoginRequiredMinin,View):
    '''提交订单页面显示'''
    def post(self,request):
        # 获取登录的用户
        user = request.user
        # 获取参数的sku_ids
        sku_ids = request.POST.getlist('sku_ids')
        # 校验参数sku_ids
        if not sku_ids:
            # 跳转到购物车页面
            return redirect(reverse('carts:cart'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        skus = []
        # 保存商品的总件数和总价格
        total_count = 0
        total_price = 0
        # 遍历sku_ids获取用户购买的商品信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户购买商品的数量
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price*int(count)
            # 动态给sku增加属性count，保存商品的数量
            sku.count = int(count)
            # 动态给sku增加属性amount，保存商品的小计
            sku.amount = int(amount)
            # 追加进去
            skus.append(sku)
            # 累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += int(amount)

        # 运费（本应该是一个单独的子系统），本项目写死
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文
        sku_ids = ','.join(sku_ids)
        context = {'skus':skus,
                   'total_count':total_count,
                   'total_price':total_price,
                   'transit_price':transit_price,
                   'total_pay':total_pay,
                   'addrs':addrs,
                   'sku_ids':sku_ids}

        # 使用模板
        return render(request,'place_order.html',context)


# 前端传递的参数：地址（addr_id）,支付方式（pay_method）,用户要购买的商品id字符串（sku_ids）
# /order/commit
class OrderCommitView(View):
    '''订单创建'''
    # django对数据库的事务进行开启
    @transaction.atomic
    def post(self,request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res':1, 'errmsg':'参数不完整'})

        # 校验支付方式
        # if pay_method not in OrderInfo.PAY_METHODS.keys():
        #     return JsonResponse({'res':2, 'errmsg':'非法的支付方式'})
        if pay_method != "3":
            return JsonResponse({'res':2, 'errmsg':'暂时只支持支付宝付款'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Exception:
            return JsonResponse({'res':3, 'errmsg':'地址非法'})

        # todo: 创建订单核心业务

        # 组织参数
        # 订单格式：当时时间+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()

        try:
            # todo: 向df_order_info 表中加入一条记录
            order = OrderInfo.objects.create(order_id = order_id,
                                             user = user,
                                             addr = addr,
                                             pay_method = pay_method,
                                             total_count = total_count,
                                             total_price = total_price,
                                             transit_price = transit_price)

            # todo: 用户的订单中有几个商品就需要向df_order_goods表中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品的信息
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except:
                    # 商品不存在
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':4, 'errmsg':'商品不存在'})

                # 从redis中获取用户所要购买的商品数量
                count = conn.hget(cart_key, sku_id)

                # todo: 判断商品的库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':6,'errmsg':'商品库存不足'})

                # todo:向df_order_goods表中加入一条记录
                OrderGoods.objects.create(order = order,
                                          sku = sku,
                                          count = count,
                                          price = sku.price)

                # todo: 更新商品的库存和容量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # todo: 累加计算订单商品的总数量和总价格
                amount = sku.price*int(count)
                total_count += int(count)
                total_price += int(amount)

            # todo: 更新订单信息表中的商品的总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res':7, 'errmsg':'下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # todo: 清除用户购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res':5, 'message':'创建成功'})



class OrderPayView(View):
    '''订单支付'''
    def post(self,request):
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res':1,'errmsg':'无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id = order_id,
                                          user = user,
                                          pay_method = 3,
                                          order_status = 1)
        except Exception:
            return JsonResponse({'res':2,'errmsg':'订单错误'})

        # 业务处理
        # with open(r'E:/github/Meicai_web/dailyfresh/apps/order/app_private_key.pem','r') as f:
        #     app_private_key_string = f.read()
        # with open(r'E:/github/Meicai_web/dailyfresh/apps/order/alipay_public_key.pem','r') as f:
        #     alipay_public_key_string = f.read()

        app_private_key_string = open("E:/github/Meicai_web/dailyfresh/apps/order/app_private_key.pem").read()
        alipay_public_key_string = open("E:/github/Meicai_web/dailyfresh/apps/order/alipay_public_key.pem").read()

        alipay = AliPay(
            appid="2021000121673359",
            app_notify_url=None,  # 默认回调 url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认 False
            verbose=False,  # 输出调试数据
            # config=AliPayConfig(timeout=15)  # 可选，请求超时时间
        )
        # 调用支付接口
        total_pay = order.total_price + order.transit_price
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单号
            total_amount=str(total_pay),  # 价格
            subject='天天生鲜_%s'%order_id,  # 名称
            return_url=None,  # 支付成功后会跳转的页面
            notify_url=None,  # 回调地址，支付成功后支付宝会向这个地址发送post请求
        )
        # response = alipay.api_alipay_trade_query(out_trade_no=order_id)
        # print(response)
        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?'+order_string
        return JsonResponse({'res':3,'pay_url':pay_url})



# ajax post
# 前端传递的参数：订单id（order_id）
# /order/check
class CheckPayView(View):
    '''查看订单支付的结果'''
    def post(self,request):
        '''查询支付结果'''
        # 用户是否登录
        # print("查询支付结果")
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        # print(order_id)

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except Exception:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务处理
        # with open(r'E:/github/Meicai_web/dailyfresh/apps/order/app_private_key.pem','r') as f:
        #     app_private_key_string = f.read()
        # with open(r'E:/github/Meicai_web/dailyfresh/apps/order/alipay_public_key.pem','r') as f:
        #     alipay_public_key_string = f.read()
        app_private_key_string = open("E:/github/Meicai_web/dailyfresh/apps/order/app_private_key.pem").read()
        alipay_public_key_string = open("E:/github/Meicai_web/dailyfresh/apps/order/alipay_public_key.pem").read()

        alipay = AliPay(
            appid="2021000121673359",
            app_notify_url=None,  # 默认回调 url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认 False
            verbose=False,  # 输出调试数据
            config=AliPayConfig(timeout=15)  # 可选，请求超时时间
        )

        print("准备进入循环")
        while True:
            # 调用支付宝的交易查询接口
            response = alipay.api_alipay_trade_query(order_id)
            print(response)
            code = response.get("code")
            trade_status = response.get("trade_status")

            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4 # 待评价
                order.save()
                # 返回结果
                print("支付成功了")
                return JsonResponse({'res':3, 'message':'支付成功'})
            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败 但过会会成功
                time.sleep(5)
                continue
            else:
                # 支付出错
                return JsonResponse({'res':4, 'errmsg':'支付失败'})








