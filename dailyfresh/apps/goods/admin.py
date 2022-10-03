from django.contrib import admin
from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner,GoodsSKU,Goods
from django.core.cache import cache
# Register your models here.

class BaseModelAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        """新增或修改数据时调用"""
        super().save_model(request,obj,form,change)

        # admin 后台清除缓存
        cache.delete("index_page_data")

    def delete_model(self, request, obj):
        """删除数据时调用"""
        super().delete_model(request,obj)

        # admin 后台清除缓存
        cache.delete("index_page_data")


admin.site.register(GoodsType,BaseModelAdmin)
admin.site.register(IndexGoodsBanner,BaseModelAdmin)
admin.site.register(IndexPromotionBanner,BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner,BaseModelAdmin)
admin.site.register(GoodsSKU,BaseModelAdmin)
admin.site.register(Goods,BaseModelAdmin)

