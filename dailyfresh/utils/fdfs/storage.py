from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings
class FDFSStorage(Storage):
    """fast dfs文件存储类"""
    def __init__(self,client_conf=None,base_url=None):
        # 定义conf和url
        if client_conf is None:
            client_conf = "./utils/fdfs/client.conf"
        self.client_conf = settings.FDFS_CLIENT_CONF
        if base_url is None:
            base_url = "http://140.83.37.178:8888/"
        self.base_url = settings.FDFS_URL


    def _open(self,neme,mode="rb"):
        """打开文件的使用"""
        pass

    def _save(self,name,content):
        """保存文件的使用"""
        # name：上传文件的名字
        # content：上传文件内容的File对象

        # 创建一个Fdfs_client对象
        client = Fdfs_client(self.client_conf)

        # 上传文件到fastdfs系统中
        res = client.upload_by_buffer(content.read())

        if res.get("Status")!= "Upload successed.":
            # 上传失败
            raise Exception("上传文件到fast dfs失败")

        # 获取返回文件的id
        filename = res.get("Remote file_id")
        return filename

    def exists(self,name):
        """Django判断文件名是否可用"""
        return False

    def url(self, name):
        return self.base_url+name