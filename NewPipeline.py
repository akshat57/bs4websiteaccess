from WebsiteAccessModule import WebsiteAccessModule
from bs4 import BeautifulSoup
from LeadershipInfoExtraction import Webpage
from SeleniumChrome import ChromeDriver
import json


def read_file(filename = 'Complete_ICM_List'):

    websites = []

    with open(filename) as file:
        for i, line in enumerate(file):
            if i == 0:
                continue
            line = line.strip().split('\t')

            if len(line) > 1:
                websites.append((line[0].strip(), line[1].strip())  )

    return websites

def read_superultra(filename = 'superultralist'):
    all_websites = read_file()

    superultra_clients = []
    with open(filename) as file:
        for line in file:
            line = line.strip()
            superultra_clients.append(line)

    superultra_websites = []
    for (client, website) in all_websites:
        if client in superultra_clients:
            superultra_websites.append((client, website))

    return superultra_websites





if __name__ == '__main__':

    website_access_logs = "Logs/website_access.txt"
    proxyDict = {"http": 'http://approxy.jpmchase.net:8080', "https": 'http://approxy.jpmchase.net:8080'}
    header = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
    website_access_module = WebsiteAccessModule(proxyDict, header, website_access_logs)

    store_stats = []
    superultra = read_superultra()
    websites = read_file()
    access_counter = 0
    executive_found = 0
    list_of_executives = {}

    n_leadership_detected, n_has_class, n_tree_source_found = 0,0,0
    write_data = True

    if write_data:
        version = 'sel' + str(102)
        json_filename = 'Data/list_of_executives_v' + version + '2.json'
        stats_filename = 'Data/stats_storage_v' + version + '2.txt'
        f = open(stats_filename, 'w')
        f.close()

    print(len(websites))

    for i, (client, website) in enumerate(websites):
        #if i + 1 <= 84:
        #    continue
        #print(i, website)

        current_stats = client + '\t' + website + '\t'
        executive_team = None

        #Access using bs4
        no_access, status_code, successful_access, failed_access, request_element = website_access_module.open_website(website)

        if successful_access:
            current_stats += 'TRUE' + '\t'
            access_counter += 1

            html_soup = BeautifulSoup(request_element.content, 'html5lib')

            webpage = Webpage(client, website, html_soup)
            webpage.find_executives()
            executive_team = webpage.executive_team



        if not executive_team:#this includes the else condition for unsuccessful access in bs4
            try:
                browser = ChromeDriver().get_driver()
                browser.get(website)
                html_content = browser.page_source
                html_soup = BeautifulSoup(html_content, 'html5lib')

                webpage = Webpage(client, website, html_soup)
                webpage.find_executives()
                executive_team = webpage.executive_team

            except:
                pass

        ####STORING STATS#####
        if executive_team:
            current_stats += 'TRUE' + '\t'
            executive_found += 1
            list_of_executives[website] = executive_team

            if write_data:
                with open(json_filename, 'w') as fp:
                    json.dump(list_of_executives, fp,  indent=4)

        else:
            current_stats += 'FALSE' + '\t'


        print(i+1, access_counter, executive_found, website)

        if write_data:
            #write stats folder
            store_stats.append(current_stats + '\n')

            f = open(stats_filename, 'a')
            f.write(current_stats + '\n')
            f.close()



