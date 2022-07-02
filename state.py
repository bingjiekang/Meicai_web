import tornado.ioloop
import tornado.web
from tornado.options import define,options
import tornado.httpserver
define("port",type=int,default=8088,help="运行这个地址和端口号")

class IndexHeadle(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class show_new(tornado.web.RequestHandler):

    def get(self):
        self.render("new.html")


setting = {

    "static_path":"images"

}


urls = [(r"/index",IndexHeadle),
        (r"/new",show_new),]


def main():
    tornado.options.parse_command_line()
    app = tornado.web.Application(urls,**setting)
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ =="__main__":
    main()