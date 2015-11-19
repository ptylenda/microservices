import json
import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.ioloop
import tornado.locks
import tornado.queues
import requests


def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


class GetResponseConnector(object):
    token = ""  # Some dead test account

    def get(self, path,):
        auth_headers = {'X-Auth-Token': 'api-key ' + self.token}
        return requests.get(self._url(path), headers=auth_headers)

    def head(self, path):
        auth_headers = {'X-Auth-Token': 'api-key ' + self.token}
        return requests.head(self._url(path), headers=auth_headers)

    @staticmethod
    def _url(path):
        return 'http://api.getresponse.com/v3' + path


class GetResponseConnectorAsync(object):
    token = ""  # Some dead test account

    def get(self, path):
        auth_headers = {'X-Auth-Token': 'api-key ' + self.token}
        return tornado.httpclient.HTTPRequest(url=self._url(path), headers=auth_headers,  connect_timeout=600, request_timeout=600)

    def head(self, path, extra_headers):
        auth_headers = {'X-Auth-Token': 'api-key ' + self.token}
        return tornado.httpclient.HTTPRequest(url=self._url(path), headers=merge_dicts(auth_headers, extra_headers))

    @staticmethod
    def _url(path):
        return 'http://api.getresponse.com/v3' + path


class CampaignToListsMapper(object):
    def map(self, campaigns_json):
        return campaigns_json


'''
class BaseResource(object):
    def __init__(self, path, connector, mapper):
        self.path = path
        self.connector = connector
        self.mapper = mapper

    def on_get(self, req, resp):
        """
        :type req: falcon.Request
        :param req:
        :type resp: falcon.Response
        :param resp:
        :return:
        """
        api_resp = self.connector.get(self.path)
        # parse errors here
        mapped_json = self.mapper.map(api_resp.json())
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(mapped_json)


class ListsResource(BaseResource):
    def __init__(self, connector=GetResponseConnector(), mapper=CampaignToListsMapper()):
        super().__init__("/campaigns/", connector, mapper)

'''


class StreamingHandler(tornado.web.RequestHandler):

    client = tornado.httpclient.AsyncHTTPClient(max_clients=5)
    connector_async = GetResponseConnectorAsync()

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        connector = GetResponseConnector()
        resp = connector.head("/contacts?perPage={0}".format(1000))
        count = int(resp.headers['TotalPages']);

        print(count)

        yield [self.flush_page(page) for page in range(1, count + 1)]

        self.finish()


    @tornado.gen.coroutine
    def flush_page(self, page):
        print("processing", page)
        req = self.connector_async.get(path="/contacts?perPage={0}&page={1}".format(1000, page))
        resp = yield self.client.fetch(req)
        print("flushing", page)
        self.write(resp.body)
        self.flush()

app = tornado.web.Application([
    (r"/lists", StreamingHandler)
])
