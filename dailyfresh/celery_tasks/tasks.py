# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
# 创建celery的一个实例对象
app = Celery("celery_tasks.tasks",broker= "redis://127.0.0.1:6379/8")

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()
# 发送激活邮件
@app.task
def send_register_active_email(to_email,username,token):
    # 发送邮件
    subject = "天天生鲜注册信息"  # 邮件标题
    message = ""
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s,欢迎成为天天生鲜注册会员<h1/><br/><a href="http://127.0.0.1:8000/user/active/%s">请点击以下链接来激活您的账户<br/>http://127.0.0.1:8000/user/active/%s<a/>' % (
    username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)

