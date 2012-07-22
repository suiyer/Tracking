import os, sys
import logging
from datetime import datetime, timedelta

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options

from handlers.helloworld import HelloWorldHandler


define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run tornado in debug mode", type=bool)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            tornado.web.URLSpec(r'/hello$', HelloWorldHandler),
            tornado.web.URLSpec(r'/status$', StatusHandler),

            tornado.web.URLSpec(r'.*', NotFoundHandler),
        ]

        current_dir = os.path.dirname(__file__)
        settings = dict(
            cookie_secret='UvDlVC4cQoaBSLjTBIlD9PTK3HqZb0ukt/WL9k/SREU=',
            template_path=os.path.join(current_dir, 'templates'),
            static_path=os.path.join(current_dir, 'static'),
            xsrf_cookies=True,
            debug=options.debug,
            gzip=True,
            autoescape='xhtml_escape'
        )

        self._clients = {}
        super(Application, self).__init__(handlers, **settings)

        logging.info('Server started on port {0}'.format(options.port))


class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        self.finish('ONLINE')


class NotFoundHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('404.html')


def run_server():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

# Start the server
if __name__ == "__main__":
    run_server()

