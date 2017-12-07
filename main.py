import json
import os, os.path
import requests
import cherrypy
from cherrypy.process.plugins import BackgroundTask
from jinja2 import Environment, FileSystemLoader
from redis import from_url

CONFIG = dict(
    REDIS_HOST=os.environ.get('REDIS_URL', 'localhost'),
    REDIS_PORT=os.environ.get('REDIS_PORT', 6379),
    REDIS_DB=os.environ.get('REDIS_DB', 0),
)
connection = from_url(CONFIG['REDIS_HOST'])

env = Environment(
    loader=FileSystemLoader('templates')
)

class NiftyStats(object):
    """Display the values stored in Redis"""

    def data_scrape():
        """Scrape the 'Nifty 50' table values"""

        URL = "https://www.nseindia.com/live_market/dynaContent/live_analysis/gainers/niftyGainers1.json"
        try:
            res = requests.get(URL)
            res_json = res.json()
            time, data = res_json['time'], res_json['data']
            data = json.dumps(data)
            return time, data

        except Exception as err:
            print ("Error in getting data")


    def data_persist():
        """Persist the data into a redis instance"""
        time, data = webapp.data_scrape()
        try:
            connection.set('data', data)
            connection.set('time', time)
            print('Data Persisted Successfully at %s'% time)

        except Exception as err:
            print('Error Persisting to a redis instance: %s'% err)

    def data_read():
        """Read the Data"""
        try:
            data = connection.get('data')
            time = connection.get('time')

            if data and time:
                data = json.loads(data.decode("utf-8"))
                time = time.decode("utf-8")
            else:
                webapp.data_persist()
            return time,data

        except Exception as err:
            print ("Error in Reading data from Redis")

    @cherrypy.expose
    def index(self):
        time, data = webapp.data_read()
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
