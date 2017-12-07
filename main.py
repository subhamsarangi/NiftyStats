import cherrypy
from cherrypy.process.plugins import BackgroundTask
import os, os.path
from jinja2 import Environment, FileSystemLoader
from scraper import *

env = Environment(
    loader=FileSystemLoader('templates')
)

class NiftyStats(object):
    """Display the values stored in Redis"""
    def __init__(self):
        self.background_task()

    def background_task(self):
        task = BackgroundTask(20, data_persist())
        task.start()

    @cherrypy.expose
    def index(self):
        data,time = data_read()
        stock_data = {'data': data,'time': time}
        home = env.get_template('index.html')
        return home.render(**stock_data)


if __name__ == '__main__':
    """Start CherryPy"""

    webapp = NiftyStats()
    conf = {
        #'global': {
        #    'server.socket_host': '0.0.0.0',
        #    'server.socket_port': int(os.environ.get('PORT', 5000)),
        #},
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        }
    }
    cherrypy.quickstart(webapp, '/', conf)

    #cherrypy.engine.start()
    #cherrypy.engine.block()
