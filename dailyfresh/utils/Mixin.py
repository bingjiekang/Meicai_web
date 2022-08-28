from django.contrib.auth.decorators import login_required

class LoginRequiredMinin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view方法
        view = super(LoginRequiredMinin,cls).as_view(**initkwargs)
        return login_required(view)