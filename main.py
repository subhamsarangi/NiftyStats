import json
import os, os.path
import requests
from urllib3 import parse
import cherrypy
from cherrypy.process.plugins import BackgroundTask
from jinja2 import Environment, FileSystemLoader
import redis


url = parse(os.environ.get('REDISTOGO_URL', 'redis://localhost'))
connection = redis.Redis(host=url.hostname, port=url.port, db=0, password=url.password)

env = Environment(
    loader=FileSystemLoader('templates')
)

class NiftyStats(object):
    """Display the values stored in Redis"""
    URL = "https://www.nseindia.com/live_market/dynaContent/live_analysis/gainers/niftyGainers1.json"

    def data_scrape(self):
        """Scrape the 'Nifty 50' table values"""
        try:
            res = requests.get(self.URL)
            res_json = res.json()
            time, data = res_json['time'], res_json['data']
            data = json.dumps(data)
            return time, data

        except Exception as err:
            print ("Error in getting data")


    def data_persist(self):
        """Persist the data into a redis instance"""
        time, data = self.data_scrape()
        try:
            connection.set('data', data)
            connection.set('time', time)
            print('Data Persisted Successfully at %s'% time)

        except Exception as err:
            print('Error Persisting to a redis instance: %s'% err)

    def data_read(self):
        """Read the Data"""
        data = connection.get('data')
        time = connection.get('time')

        if data and time:
            data = json.loads(data.decode("utf-8"))
            time = time.decode("utf-8")
        else:
            self.data_persist()

        return time,data

    @cherrypy.expose
    def index(self):
        time, data = self.data_read()
        stock_data = {'data': data,'time': time}
        home = env.get_template('index.html')
        return home.render(**stock_data)


if __name__ == '__main__':
    """Start CherryPy"""

    webapp = NiftyStats()
    conf = {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': int(os.environ.get('PORT', 5000)),
        },
        #'/': {
        #    'tools.sessions.on': True,
        #    'tools.staticdir.root': os.path.abspath(os.getcwd())
        #},
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        }
    }

    task = BackgroundTask(5*60, webapp.data_persist, bus=cherrypy.engine)
    task.start()

    cherrypy.quickstart(webapp, '/', conf)
    cherrypy.engine.start()
