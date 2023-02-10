import re
from bs4 import NavigableString, BeautifulSoup
from DetectExecutive import DetectExecutive
import spacy
from SeleniumChrome import ChromeDriver
from time import sleep
from random import uniform

class Webpage(DetectExecutive):
    def __init__(self, client, website, html_soup, title_pattern = None):
        self.client = client
        self.website = website
        self.html_soup = html_soup
        self.nlp = spacy.load("en_core_web_sm")
        self.search_depth_max = 15

        #assign ceo search pattern
        if title_pattern:
            self.title_pattern = title_pattern
        else:
            self.title_pattern = r"^\s*Managing Partner\b|^\s*CEO\b|^\s*Chief Executive Officer\b|^\s*President\b|^\s*Founder\b|^\s*Co-Founder\b|^\s*Founding Principal\b|^\s*Director\b|^\s*Chief Technology Officer\b|^\s*Chief Financial Officer\b|\s*Principal\b|\s*Manager\b|\s*Partner\b|\s*Vice Chairman\b|\s*Head of Marketing\b|\s*Managing Member\b|\s*Chief Investment Officer\b"

        self.has_class = False
        self.tree_source_found = False
        self.executive_team = {}



    def find_executives(self):
        #print('HERE')
        for elem in self.html_soup.find_all(text=re.compile(self.title_pattern)):
            if len(self.executive_team) > 20:
                break

            leadership_info, leadership_detected, elem, name_tag, title_tag, is_image_link_detected, is_profile_link_detected = self.find_personnel(elem)
            #print(leadership_detected)
            if leadership_detected:
                name = list(leadership_info.keys())[0]
                #print('Original exec:', name, name_tag.name, leadership_info[name]['title'], title_tag.name, is_profile_link_detected)
                self.executive_team[name] = leadership_info[name]

                #go to parent if current tag does not have a class name
                class_search_depth = 0
                while elem and not elem.has_attr('class') and class_search_depth < self.search_depth_max:
                    elem = elem.parent
                    class_search_depth += 1

                #print('POST CHECKING IF ELEMENT HAS CLASS', elem.has_attr('class'), elem['class'][0])

                #code if element found has a class
                if elem and elem.has_attr('class'):
                    tree_source_found = False
                    found_element = None
                    search_depth = 0

                    #Find tree source node
                    while not tree_source_found and elem.has_attr('class') and search_depth < 4:
                        if len(elem['class']):
                            query_class_name = elem['class'][0]
                            tree_source_found, found_element = self._find_source_node(elem, query_class_name)

                            if not tree_source_found:
                                elem = elem.parent
                                search_depth += 1
                        else:
                            break

                    #if tree source is found, and if elem != None, then check itself and its siblings. They have the team info.
                    # To do so --> Go to parent and check all direct children.
                    if found_element and tree_source_found:
                        elem = found_element.parent

                        #print('FINAL SOURCE', elem['class'][0])

                        for child in elem.find_all(recursive=False):
                            if child:
                                #print(child['class'][0], name_tag.name, title_tag.title)
                                is_detected_name, detected_name, is_detected_title, detected_title, is_detected_profile, detected_profile_link, is_detected_image, detected_image_link, bio = self.search_children(child, name_tag, title_tag, self.title_pattern, self.website)

                                #save executive team
                                if is_detected_name:
                                    if detected_name not in self.executive_team:
                                        self.executive_team[detected_name] = {}
                                    if ('title' not in self.executive_team[detected_name] or not len(self.executive_team[detected_name]['title']) ) and is_detected_title:
                                        self.executive_team[detected_name]['title'] = detected_title
                                    if 'profile_link' not in self.executive_team[detected_name] and is_detected_profile:
                                        self.executive_team[detected_name]['profile_link'] = detected_profile_link
                                    if len(bio):
                                        self.executive_team[detected_name]['bio'] = bio
                                    if 'image_link' not in  self.executive_team[detected_name] and is_detected_image:
                                        self.executive_team[detected_name]['image_link'] = detected_image_link

                    else:
                        pass
                        #print('No class!!!!!!!')
                        #print(executive_team)

        #Call do image search function
        for exec in self.executive_team:
            if 'image_link' not in self.executive_team[exec].keys():
                company_name = self.client
                exec_name = exec
                query = [exec_name, company_name]

                image_link = self.do_image_search_sel(query)
                if image_link:
                    self.executive_team[exec]['image_link'] = image_link


    def do_image_search_sel(self, query, top_N = 5, sleep_time = 3):
        #sanity sleep
        sleep(uniform(0, sleep_time))

        #query is generated as follows
        exec_name = query[0]
        company_name = query[1]
        query = exec_name + ' ' + company_name
        search_url = 'https://www.google.com/search?as_st=y&tbm=isch&as_q=' + query + '&as_epq=&as_oq=&as_eq=&imgsz=&imgar=&imgc=&imgcolor=&imgtype=&cr=&as_sitesearch=&safe=images&as_filetype=&tbs='

        try:
            browser = ChromeDriver().get_driver()
            browser.get(search_url)
            html_content = browser.page_source
        except:
            return None

        soup = BeautifulSoup(html_content, 'html5lib')
        table = soup.findAll('a')

        check_counter = 0       #only check the first three results with image and description
        for i, row in enumerate(table):
            for img_tag in row.find_all('img'):
                url, desc = None, None
                if img_tag.has_attr('src'):
                    url = img_tag['src']
                if img_tag.has_attr('alt'):
                    desc = img_tag['alt']

                if url and desc:
                    check_counter += 1

                    #find exec name in description
                    desc = desc.lower()
                    executive_name = exec_name.lower().split(' ')
                    name_found = False

                    for name in executive_name:
                        if len(name) > 2:#not searching for initials
                            if desc.find(name) != -1:
                                name_found = True
                                break

                    ###
                    if name_found:
                        return url

            if check_counter > 2:
                break



        return None


    #########################################################ADDITIONAL METHODS###########################################################


    def _find_source_node(self, elem, query_class_name):
        search_depth = 0
        tree_source_found = False

        #Find source node of current leader found
        while search_depth < self.search_depth_max:

            #search all siblings to search for current class name
            if elem and elem.next_siblings:
                for sibling in elem.next_siblings:
                    if sibling and not isinstance(sibling, NavigableString) and not tree_source_found:
                        if self._check_all_children(sibling, query_class_name):
                            tree_source_found = True
                            break

            if elem and elem.prev_siblings:
                for sibling in elem.prev_siblings:
                    if sibling and not isinstance(sibling, NavigableString) and not tree_source_found:
                        #check if any child of the sibling has the query class name
                        if self._check_all_children(sibling, query_class_name):
                            tree_source_found = True
                            break

            if tree_source_found or elem == None:
                break
            else:
                elem = elem.parent
                search_depth += 1

        return tree_source_found, elem


    def _check_all_children(self, query_tag, query_class_name):
        '''Check all children of a current tag for the presence of a query class name.'''

        query_class_found = False

        children_searched = 0
        for tag in query_tag.find_all():
            children_searched += 1
            if tag and not isinstance(tag, NavigableString) and tag.has_attr('class') and len(tag['class']) and tag['class'][0] == query_class_name:
                query_class_found = True
                break

        return query_class_found










