import re
from bs4 import NavigableString, BeautifulSoup
from WebsiteAccessModule import WebsiteAccessModule
from DetectFeatures import DetectPerson, DetectImageLink, DetectProfileLink

class DetectExecutive(DetectPerson, DetectImageLink, DetectProfileLink):
    def __init__(self):
        pass

    def find_personnel(self, elem):
        leadership_detected = False
        leadership_info = {}
        exec_details = {}
        search_depth = 0

        is_name_detected = False
        name_tag = None
        is_title_detected = False
        title_tag = None
        is_bio_detected = False
        is_profile_link_detected = False
        is_image_link_detected = False

        # Assumption: all the related info should be under the same DOM tree branch
        # Step 1: Based on the detected CEO text string, search upwards to find name, title, profile and image
        elem = elem.parent

        while (elem is not None) and (search_depth < self.search_depth_max):
            for tag in elem.children:
                if not is_name_detected:
                    is_name_detected, name_str = self.detect_name(tag)
                    if is_name_detected:
                        leadership_info['name'] = name_str
                        name_tag = tag
                        while isinstance(name_tag, NavigableString):
                            name_tag = name_tag.parent

                if not is_title_detected:
                    is_title_detected, title_str = self.detect_title(tag)
                    if is_title_detected:
                        leadership_info['title'] = title_str
                        title_tag = tag
                        while isinstance(title_tag, NavigableString):
                            title_tag = title_tag.parent

                if is_name_detected and is_title_detected and not is_bio_detected:
                    bio_str = self.detect_bio(tag, leadership_info['name'], leadership_info['title'], '')
                    if len(bio_str):
                        leadership_info['bio'] = bio_str
                        is_bio_detected = True

            if is_name_detected and not is_image_link_detected:
                is_image_link_detected, image_link = self.detect_image_link(elem, name_str)
                if is_image_link_detected:
                    leadership_info['image_link'] = self._process_link(image_link, self.website)

            if is_name_detected and not is_profile_link_detected:
                is_profile_link_detected, profile_link = self.detect_profile_link(elem, name_str)
                if is_profile_link_detected:
                    leadership_info['profile_link'] = self._process_link(profile_link, self.website)

            leadership_detected = is_name_detected & is_title_detected

            if leadership_detected:
                break

            elem = elem.parent
            search_depth = search_depth + 1

        # Assumption: sometime, image tag is not in same branch of DOM with name and title

        # Step 2: search all the string ending with jpg
        if is_name_detected and is_profile_link_detected:

            if not is_bio_detected:
                current_bio = self.get_bio_from_profile_link(leadership_info['profile_link'], leadership_info['name'])
                if len(current_bio):
                    leadership_info['bio'] = current_bio

            if not is_image_link_detected:
                is_image_link_detected, image_link = self.get_image_from_profile_link(leadership_info['profile_link'], leadership_info['name'])
                if is_image_link_detected:
                    leadership_info['image_link'] = self._process_link(image_link, self.website)

        if leadership_detected:
            exec_details[leadership_info['name']] = {}

            for property in leadership_info:
                if property != 'name':
                    exec_details[leadership_info['name']][property] = leadership_info[property]

        return exec_details, leadership_detected, elem, name_tag, title_tag, is_image_link_detected, is_profile_link_detected


    def search_children(self, sibling, name_tag, title_tag, ceo_pattern, website):
        is_detected_name, detected_name, is_detected_title, detected_title, is_detected_profile, detected_profile_link, is_detected_image, detected_image_link = False, None, False, None, False, None, False, None
        current_bio = ''

        if sibling and not isinstance(sibling, NavigableString):
            #detect name
            for tag in sibling.find_all(name_tag.name):
                is_detected_name, detected_name = self.detect_name(tag)
                if is_detected_name:
                    break

            if is_detected_name:
                #detect title
                for tag in sibling.find_all(title_tag.name):
                    is_detected_title, detected_title = self.find_title_in_siblings(tag, detected_name)
                    if is_detected_title:
                        break

                if not is_detected_title:
                    for tag in sibling.find_all(title_tag.name):
                        is_detected_title, detected_title = self.detect_title(tag)
                        if is_detected_title:
                            break

                #detect image link
                for tag in sibling.find_all():
                    is_detected_image, detected_image_link = self.detect_image_link(tag, detected_name)
                    if is_detected_image:
                        detected_image_link = self._process_link(detected_image_link, website)
                        break

                #detect profile link
                #profile link is only looked for in the 'a' tag
                if sibling.name == 'a':
                    is_detected_profile, detected_profile_link = self.detect_profile_link(sibling, detected_name)
                    if is_detected_profile:
                        detected_profile_link = self._process_link(detected_profile_link, website)

                if not is_detected_profile:
                    for tag in sibling.find_all():
                        is_detected_profile, detected_profile_link = self.detect_profile_link(tag, detected_name)
                        if is_detected_profile:
                            detected_profile_link = self._process_link(detected_profile_link, website)
                            break

                #if profile link found, go there to search for bio
                if is_detected_profile:
                    current_bio = self.get_bio_from_profile_link(detected_profile_link, detected_name)
                    is_detected_image, detected_image_link = self.get_image_from_profile_link(detected_profile_link, detected_name)
                    if is_detected_image:
                        detected_image_link = self._process_link(detected_image_link, website)


            #check for bio only when there is no profile link. If there is profile link, bio is in the profile link
            if is_detected_name and not is_detected_profile:
                for tag in sibling.find_all():
                    current_bio = self.detect_bio(tag, detected_name, detected_title, current_bio)

        #print('before returning:', is_detected_image, detected_image_link)
        return is_detected_name, detected_name, is_detected_title, detected_title, is_detected_profile, detected_profile_link, is_detected_image, detected_image_link, current_bio



    def get_bio_from_profile_link(self, profile_link, name):
        #first process the profile link so that it is a legitimate website
        proxyDict = {"http": 'http://approxy.jpmchase.net:8080', "https": 'http://approxy.jpmchase.net:8080'}
        header = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
        website_access_module = WebsiteAccessModule(proxyDict, header)

        no_access, status_code, successful_access, failed_access, request_element = website_access_module.open_website(profile_link)
        person_profile = ''

        if successful_access:
            profile_soup = BeautifulSoup(request_element.content, 'html5lib')

            #only making searches with first and last name
            first_name = name.split(' ')[0]
            last_name = name.split(' ')[-1]

            for tag in profile_soup(text = re.compile(first_name + '|' + last_name + '|' + name) ):
                profile_text = tag.text.strip()
                for text in profile_text.split('\n'):
                    processed_bio = self.process_bio(text)#Needs to inherit from DetectPerson class
                    if len(processed_bio) and (len(processed_bio) > (50 + len(name)) ) and person_profile.find(processed_bio) == -1:
                        person_profile += processed_bio + '\n'

            person_profile = person_profile.strip()

        return person_profile

    def get_image_from_profile_link(self, profile_link, name):

        #first process the profile link so that it is a legitimate website
        proxyDict = {"http": 'http://approxy.jpmchase.net:8080', "https": 'http://approxy.jpmchase.net:8080'}
        header = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
        website_access_module = WebsiteAccessModule(proxyDict, header)

        no_access, status_code, successful_access, failed_access, request_element = website_access_module.open_website(profile_link)

        is_detected_image, detected_image_link = False, None
        if successful_access:
            profile_soup = BeautifulSoup(request_element.content, 'html5lib')
            for tag in profile_soup.find_all('img'):
                is_detected_image, detected_image_link = self.detect_image_link(tag, name)
                if is_detected_image:
                    break

        return is_detected_image, detected_image_link


    ############################ADDITIONAL FUNCTIONS###############################################################
    def _process_link(self, link, website):
        processed_link = link.strip().replace(' ', '%20')
        domain = self._get_domain(website)

        if processed_link[0:2] == '//':
            processed_link = link
        elif processed_link[0] == '/':
            processed_link = domain + link
        elif processed_link[0:2] == './':
            processed_link = domain + link[1:]
        elif processed_link[0:3] == '../':
            processed_link = '/'.join(website.split('/')[:-2]) + processed_link[2:]
        elif processed_link[-1] == '#':
            processed_link = website + processed_link[:-1] + '/'

        return processed_link

    def _get_domain(self, website):
        website = website.strip()
        if website.find('/') != -1:
            parts = website.split('/')
            domain = parts[0] + '//' + parts[2]
        else:
            domain = website

        return domain
