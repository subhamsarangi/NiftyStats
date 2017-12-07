import requests
from redis import StrictRedis
import os
import json

CONFIG = dict(
    REDIS_HOST=os.environ.get('REDIS_URL', 'localhost'),
    REDIS_PORT=os.environ.get('REDIS_PORT', 6379),
    REDIS_DB=os.environ.get('REDIS_DB', 0),
)
connection = StrictRedis(CONFIG['REDIS_HOST'], CONFIG['REDIS_PORT'], CONFIG['REDIS_DB'])

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
    time, data = data_scrape()
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
            data_persist()
        return time,data

    except Exception as err:
        print ("Error in Reading data from Redis")
