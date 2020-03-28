from WP.https_request_handler import HTTPRequestHandler
from WP.proxy import Proxy

_VERSION_NON_DETECTABLE_URLS = ["/license.txt", "/wp-trackback.php", "/readme.html", "/wp-admin/upgrade.php"]

_VERSION_DETECTABLE_URLS = ['/wp-admin', '/feed']


class WPDetector(object):

    def __init__(self, domain, proxies=None):
        '''
        Keep here the domain and the test state (tested URLs, detected versions, etc) using protected attributes
        :param domain:
        :param proxies: working via HTTP proxies
        '''
        self._domain = domain
        if proxies is None:
            self._proxies = proxies
        else:
            tmp = []
            self._proxies = []
            for proxy in proxies:
                p = Proxy(proxy)
                tmp.append(p)
            self._proxies = tmp
        self._urls = _VERSION_DETECTABLE_URLS + _VERSION_NON_DETECTABLE_URLS

    def detect(self, retries=0, timeout=5, aggressive=False, urls=None, proxies=None):
        '''
        This function detects if the website on the domain runs over wordpress. if it is, it will detect the version
        :param aggressive: if aggressive is False, the maximal number of HTTP requests is len(urls) + 2
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: a tuple: (whether the domain operates over Wordpress, its version)
        '''
        if urls is None:
            urls = self._urls
        if proxies is None:
            proxies = self._proxies
        if not aggressive:
            return self.is_wordpress(urls=urls, proxies=proxies, timeout=timeout, retries=retries)
        else:
            return self.is_wordpress(urls=urls, proxies=proxies, retries=3, timeout=5)

    def is_wordpress(self, urls=None, proxies=None, timeout=5, retries=0):
        '''
        This function detects if the website runs over wordpress
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: a tuple: (whether the domain operates over Wordpress, its version)
        '''
        if not urls:
            url = 'https://' + str(self._domain)
            http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
            response = http_handler.send_http_request(method='get', url=url)
            if response is None:
                pass
            if str(response.status_code) != ('200' or '403'):
                return False, "Could'nt detect version"
            else:
                if "wordpress" in str(response.content).lower():
                    return True, "Could'nt detect version"
            return False, "Could'nt detect version"
        else:
            response_list = []
            for url in urls:
                complete_url = 'https://' + str(self._domain) + url
                http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
                response = http_handler.send_http_request(method='get', url=complete_url)
                if response is None:
                    break
                if (url in _VERSION_DETECTABLE_URLS) and (response is not None):
                    response_list.append(self.get_version(response.content, url))
                elif (url in _VERSION_NON_DETECTABLE_URLS) and (response is not None):
                    if str(response.status_code) != ('200' or '403' or '401'):
                        response_list.append((False, "Could'nt detect version"))
                    else:
                        response_list.append((True, "Could'nt detect version"))
                else:
                    if "wordpress" in str(response.content).lower():
                        response_list.append((True, "Could'nt detect version"))
                    response_list.append((False, "Could'nt detect version"))
        possible_outcomes = []
        is_word_press = False
        for item in response_list:
            if item[0]:
                possible_outcomes.append(item)
        for outcome in possible_outcomes:
            if outcome[0]:
                is_word_press = True
            if 'version' not in outcome[1]:
                return outcome
        if is_word_press:
            return True, "Could'nt detect version"
        return False, "Could'nt detect version"

    def get_version(self, data=None, url=None):
        '''
        detects the version of the wordpress
        :param data: The answer of the http request
        :param url: the suffix of the url that got the response of data
        :return: a tuple: (whether the domain operates over Wordpress, doesn't return the version)
        '''
        if not (data and url):
            return self.__get_version_standalone()
        if not (data or url):
            return True, "Could'nt detect version"
        else:
            return self.__detect_version_logic(data, url)

    def __detect_version_logic(self, data, url):
        '''
        detects the version of the wordpress
        :param data: The answer of the http request
        :param url: the suffix of the url that got the response of data
        :return: a tuple: (whether the domain operates over Wordpress, doesn't return the version)
        '''
        if "wp-admin" in str(url):
            start_index = str(data).find('"name="generator" content="WordPress"')
            if start_index != -1:
                end = data.find("'", start_index)
                version = data[start_index + 38:end]
                for letter in version:
                    if not (str(letter).isdigit() or str(letter) == '.'):
                        return True, "Could'nt detect version"
                return True, version
            return False, "Could'nt detect version"
        elif "feed" in str(url):
            start_index = str(data).find('?v=')
            if start_index != -1:
                end = str(data).find("<", start_index)
                version = str(data)[start_index + 3:end]
                for letter in version:
                    if not (str(letter).isdigit() or str(letter) == '.'):
                        return True, "Could'nt detect version"
                return True, version
            return False, "Could'nt detect version"

    def __get_version_standalone(self):
        '''
        detects the version of the wordpress
        :return: a list: (whether the domain operates over Wordpress, doesn't return the version)
        '''
        response_list = []
        for url in _VERSION_DETECTABLE_URLS:
            complete_url = 'https://' + str(self._domain) + url
            http_handler = HTTPRequestHandler(proxies=self._proxies, retries=0, timeout=5)
            response = http_handler.send_http_request(method='get', url=complete_url)
            if response in None:
                raise Exception
            response_list.append(self.__detect_version_logic(response.content, url))
        possible_outcomes = []
        outcome = None
        for item in response_list:
            if item[0]:
                # and 'version' not in str(item[1]):
                possible_outcomes.append(item)
        for outcome in possible_outcomes:
            if 'version' not in outcome[1]:
                return outcome
        return outcome
