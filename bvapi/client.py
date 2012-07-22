"""
    bvapi.py
    ~~~~~~

    Python API wrapper for the Bazaarvoice Platform API
"""

import datetime
import logging
import hashlib
from sync import async, sync_proxy
import tornado.escape
import tornado.httpclient
import types
import urllib

from dictutil import O
from normalize import Normalizer

log = logging.getLogger('bvapi')

class BvApiException(Exception):
    """ An unexpected exception from the Bazaarvoice API. """

class BvApi(object):
    """ Asynchronous client for making HTTP requests to the Bazaarvoice API """

    def __init__(self, api_key, host, proxy_host=None, encoding_key=None, staging=False, virtual_env=None, api_version='5.0', normalizer_options={}, io_loop=None):
        self._api_key = api_key
        self._scheme = 'http'
        self._host = host
        self._proxy_host = proxy_host
        self._port = 80
        self._encoding_key = encoding_key
        self._staging = staging
        self._virtual_env = virtual_env
        self._api_version = api_version
        self._normalizer_options = normalizer_options
        self._io_loop = io_loop

    @async
    def get(self, data_type, callback, error_callback=None, **kwargs):
        self._fetch('GET', data_type, kwargs, callback, error_callback)

    @async
    def get_reviews(self, callback, error_callback=None, **kwargs):
        self.get('review', callback, error_callback, **kwargs)

    @async
    def get_questions(self, callback, error_callback=None, **kwargs):
        self.get('question', callback, error_callback, **kwargs)

    @async
    def get_answers(self, callback, error_callback=None, **kwargs):
        self.get('answer', callback, error_callback, **kwargs)

    @async
    def get_stories(self, callback, error_callback=None, **kwargs):
        self.get('story', callback, error_callback, **kwargs)

    @async
    def get_authors(self, callback, error_callback=None, **kwargs):
        self.get('author', callback, error_callback, **kwargs)

    @async
    def get_products(self, callback, error_callback=None, **kwargs):
        self.get('product', callback, error_callback, **kwargs)

    @async
    def get_categories(self, callback, error_callback=None, **kwargs):
        self.get('category', callback, error_callback, **kwargs)

    @async
    def get_raw(self, data_type, callback, error_callback=None, **kwargs):
        self._fetch_raw('GET', data_type, kwargs, callback, error_callback)

    @async
    def post(self, data_type, callback, error_callback=None, **kwargs):
        self._fetch_raw('POST', data_type, kwargs, callback, error_callback)

    @async
    def post_question(self, callback, error_callback=None, **kwargs):
        self.post('question', callback, error_callback, **kwargs)

    @async
    def post_answer(self, callback, error_callback=None, **kwargs):
        self.post('answer', callback, error_callback, **kwargs)

    def encode_user(self, id, **kwargs):
        """ Encodes and signs a Bazaarvoice reviewer external ID.
        Key word args can be used to slave parameters in the user ID."""
        kwargs['userid'] = id
        kwargs['date'] = datetime.date.today().strftime('%Y%m%d')
        string = urllib.urlencode(kwargs, True)
        return hashlib.md5(self._encoding_key + string).hexdigest() + string.encode('hex')

    def _fetch(self, method, data_type, params, callback=None, error_callback=None):
        def _normalize(response):
            callback(Normalizer(self, data_type, response, **self._normalizer_options).normalize())
        self._fetch_raw(method, data_type, params, callback=_normalize, error_callback=error_callback)

    def _pluralize_data_type(self, data_type):
        """Pluralize api data types for display urls.  I love it that submission and
        display urls use different pluralization of the data type."""
        if data_type.endswith('y'):
            pluralized = data_type.rstrip('y') + 'ies'  # eg. story=>stories, category=>categories
        else:
            pluralized = data_type + 's'  # eg. review=>reviews
        return pluralized

    def _fetch_raw(self, method, data_type, params, callback=None, error_callback=None):
        query = dict()
        query['apiversion'] = self._api_version
        query['passkey'] = self._api_key
        params = [(k,v.encode('utf-8') if type(v) is types.UnicodeType else v) for (k,v) in params.items() if v is not None]
        if method != 'POST':
            query.update(params)
            body = None
            end_point = self._pluralize_data_type(data_type)
        else:
            body = urllib.urlencode(params, True)
            end_point = 'submit' + data_type

        url = '{scheme}://{host}:{port}{staging}{virtual_env}/data/{end_point}.json?{query}'.format(
            scheme=self._scheme,
            host=self._proxy_host or self._host,
            port=self._port,
            staging='/bvstaging' if self._staging else '',
            virtual_env=('/ve/' + self._virtual_env) if self._virtual_env else  '',
            end_point=end_point,
            query=urllib.urlencode(query, True)
        )
        headers = {
            'Host': self._host,
        }

        if body is None:
            log.info('request %s %s', method, url)
        else:
            log.info('request %s %s #body_bytes=%d', method, url, len(body))

        def handle_response(response):
            log.debug('response %d for %s %s', response.code, method, url)
            if response.code != 200:
                if error_callback is not None:
                    error_callback(response.code, url, None)
                    return
                else:
                    log.error('Unexpected BV API response code %d for url %s', response.code, url)
                    raise BvApiException(response.code, url)

            result = O.recursive(tornado.escape.json_decode(response.body))
            if result.HasErrors:
                code = (result.Error and result.Error.Code) or 'UNKNOWN'
                message = (result.Error and result.Error.Message) or 'Unknown error'
                if error_callback is not None:
                    error_callback(code, url, result)
                    return
                else:
                    log.error('Unexpected BV API error response %s "%s" for url %s', code, message, url)
                    raise BvApiException(code, url, result)

            callback(result)

        client = tornado.httpclient.AsyncHTTPClient(io_loop=self._io_loop)
        client.fetch(url, headers=headers, callback=handle_response, method=method, body=body)


# Synchronous version of BvApi.  This is useful for tests and ad-hoc experimentation.
SyncBvApi = sync_proxy(async_type=BvApi, exception_constructors=dict(
    error_callback=BvApiException,
))
