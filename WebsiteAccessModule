import requests
import time


class WebsiteAccessModule:
    def __init__(self, proxyDict, header, log_filename = None, n_hops = 0, max_headless_tries = 5, max_header_tries = 5, max_request_time = 60):
        self.proxyDict = proxyDict
        self.header = header
        self.log_filename = log_filename
        if self.log_filename:
            f = open(self.log_filename, 'w')
            f.close()
        self.n_hops = n_hops
        self.max_headless_tries = max_headless_tries
        self.max_header_tries = max_header_tries
        self.max_request_time = max_request_time


    def open_website(self, url):
        if url.find('http') == -1:
            link = 'http://www.' + url
        else:
            link = url

        num_headless_tries = 0
        num_header_tries = 0
        successful_access = False   # Flag for successful access. Success is 200 return code
        too_much_time = False       # Flag for if a website takes too much time to access

        # Requesting websites without header
        while num_headless_tries < self.max_headless_tries and not successful_access and not too_much_time:
            start = time.time()

            no_access, status_code, successful_access, failed_access, request_element = self.request_website_access(link)

            num_headless_tries += 1
            too_much_time = self.check_timeout(start)

        # If unsuccessful, requesting websites with headers
        if not successful_access and not too_much_time:
            while num_header_tries < self.max_header_tries and not successful_access and not too_much_time:
                start = time.time()

                no_access, status_code, successful_access, failed_access, request_element = self.request_website_access(link)

                num_header_tries += 1
                too_much_time = self.check_timeout(start)

        #Log website access
        if self.log_filename != None and self.n_hops == 0:
            self.website_access_logs(url, no_access, status_code, successful_access, failed_access, num_headless_tries, num_header_tries)

        return no_access, status_code, successful_access, failed_access, request_element



    def request_website_access(self, link):
        successful_access = False   # Success if status_code is 200
        failed_access = False       # Failed if status_code other than 200
        status_code = -1            # Return value of status coded
        no_access = False           # No Access when an exception occurs during request
        request_element = None      # Request element for beautifulsoup

        try:
            r = requests.get(link, proxies = self.proxyDict, headers = self.header)
            status_code = r.status_code

            if r.status_code == 200:
                successful_access = True
                request_element = r
            else:
                failed_access = True

        except:
            no_access = True

        return no_access, status_code, successful_access, failed_access, request_element


    def check_timeout(self, start):
        now = time.time()
        if now - start > self.max_request_time:
            return True
        else:
            return False

    def website_access_logs(self, url, no_access, status_code, successful_access, failed_access,  num_headless_tries, num_header_tries):
        f = open(self.log_filename, 'a')
        f.write(url + ',' + str(no_access) + ',' + str(status_code) + ',' + str(successful_access) + ',' + str(failed_access) +  ',' +  str(num_headless_tries) + ',' + str(num_header_tries) + '\n')
        f.close()


if __name__ == '__main__':

    website_access_logs = "Logs/website_access.txt"
    proxyDict = {"http": 'http://approxy.jpmchase.net:8080', "https": 'http://approxy.jpmchase.net:8080'}
    header = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
    url = 'https://www.aegon.com/home/'

    website_access_module = WebsiteAccessModule(proxyDict, header, website_access_logs)
    no_access, status_code, successful_access, failed_access, request_element = website_access_module.open_website(url)
    #no_access, status_code, successful_access, failed_access, request_element = website_access_module(url, proxyDict, header, website_access_logs)
    print(status_code, successful_access)
