import re
from bs4 import NavigableString

class DetectPerson:
    '''
    This class contains methods to detect a person. This involves detecting name, title, bios
    '''

    def __init__(self):
        pass

    def detect_name(self, tag):

        is_detected = False
        detected_name = None

        if isinstance(tag, NavigableString):
            text = tag.strip()
        else:
            text = tag.text.strip()

        if len(text) <= 5 or len(text) >= 30:
            return False, None

        doc = self.nlp(text)
        if (len(doc.ents) == 1) and (doc.ents[0].label_ == 'PERSON'):
            is_detected = True
            detected_name = doc.ents[0].text
        return is_detected, detected_name

    def detect_title(self, tag):
        is_detected = False
        detected_title = None

        if isinstance(tag, NavigableString):
            text = tag.strip()
        else:
            text = tag.text.strip()

        if len(text) <= 1 or len(text) >= 100:
            return False, None

        if len(list(self.nlp(text).sents)) > 1:
            return False, None

        if re.search(self.title_pattern, text):
            is_detected = True
            detected_title = text

        return is_detected, detected_title


    def find_title_in_siblings(self, tag, name):
        is_detected = False
        title_text = tag.text.strip()

        if len(title_text) and len(title_text) < 100:
            if title_text.find(name) != -1:
                title_text = title_text.replace(name, '').replace('\n', '').strip()

            if len(title_text):
                is_detected = True

        return is_detected, title_text


    def detect_bio(self, tag, name, title, current_bio):
        bio_text = tag.text.strip()

        for text in bio_text.split('\n'):
            len_title = 0 if title == None else len(title)
            if len(text) > len(name) + len_title + 50:#if length of text contains more than title and name. Here the text can contain both name
                text = text.replace(name, '').strip()
                if title:
                    text = text.replace(title, '').strip()

                processed_bio = self.process_bio(text)

                if len(processed_bio) and current_bio.find(processed_bio) == -1:
                    current_bio += processed_bio + '\n'

        return current_bio


    def process_bio(self, bio_line):
        processed_bio = ''

        remove_pieces = ['element', 'width', '//', '!=', '{', 'http', 'href', '===', '.log', 'img', '.id', '.js', 'onclick', '.page', '()', '.html', '.attr', '.setitem']
        found_pieces = False

        for piece in remove_pieces:
            if bio_line.lower().find(piece) != -1:
                found_pieces = True

        if not found_pieces:
            processed_bio = bio_line

        return processed_bio

##################################################################CLASS DETECTS PROFILE LINK###############################################################

class DetectProfileLink:
    '''This class contains functions to detect profile links.'''
    def __init__(self):
        pass

    def detect_profile_link(self, tag, name):
        is_detected = False
        detected_profile_link = None

        #if current tag is a
        if tag.name == 'a':
            if tag.has_attr('href'):
                url = tag['href']
                is_detected, detected_profile_link = self._detect_profile_link(url, name)

        #else look for a tag in children
        if not is_detected:
            for a in tag.find_all('a'):
                if a.has_attr('href'):
                    url = a['href']
                else:
                    continue

                is_detected, detected_profile_link = self._detect_profile_link(url, name)
                if is_detected:
                    break

        return is_detected, detected_profile_link

    def _detect_profile_link(self, url, name):
        is_detected = False
        detected_profile_link = None

        # step 1: if url is not a image file
        is_image = False
        if re.search(r"\.jpg|\.jpeg$|\.jfif$|\.pjpeg$|\.pjp$|\.png$", url):
            return is_detected, detected_profile_link

        # step 2: check the url contains the name
        has_name = False
        for name_part in name.split():
            if len(name_part) <= 2:
                continue

            if name_part.lower() in url.lower():
                has_name = True
                break

        if has_name:
            is_detected = True
            detected_profile_link = url

        return is_detected, detected_profile_link


##################################################################CLASS DETECTS IMAGE LINK###############################################################
class DetectImageLink:
    def __init__(self):
        pass

    def detect_image_link(self, tag, name):
        is_detected = False
        detected_image_link = None
        urls = []

        #step 0:: If tag itself is img tag
        if tag.name == 'img':
            if tag.has_attr('src'):
                urls.append(tag['src'])

            elif tag.has_attr('data-src'):
                urls.append(tag['data-src'])

            if len(urls):
                is_detected, detected_image_link = self._detect_image_link(urls, name)

        if not is_detected:
            urls = []
            for a in tag.find_all('a'):
                if a.has_attr('href'):
                    url = a['href']
                    urls.append(url)
                else:
                    continue
            is_detected, detected_image_link = self._detect_image_link(urls, name)

        # step 2: check <img> tags for image links
        if not is_detected:
            urls = []
            for i in tag.find_all('img'):
                if i.has_attr('src'):
                    url = i['src']
                    urls.append(url)

                if i.has_attr('data-src'):
                    url = i['data-src']
                    urls.append(url)

            is_detected, detected_image_link = self._detect_image_link(urls, name)
        # step 3: check text using regex patterns for image links
        if not is_detected:
            html_text = str(tag)
            urls = []
            pattern = r"\"([A-Za-z0-9\.\-\_\/]*?\.(jpg|jpeg|png))\""
            matches = re.findall(pattern, html_text)
            for match in matches:
                urls.append(match[0])

            if len(urls) <= 0:
                pattern = r"([A-Za-z0-9\.\_\-\/]*?\.(jpg|jpeg|png))\b"
                matches = re.findall(pattern, html_text)
                for match in matches:
                    urls.append(match[0])

            is_detected, detected_image_link = self._detect_image_link(urls, name)

        return is_detected, detected_image_link


    def _detect_image_link(self, urls, name):
        is_detected = False
        detected_image_link = None

        image_patterns = ['.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp', '.png', '.ashx']

        if not urls:
            return False, None

        clean_urls = []
        for url in urls:
            # step 1: if url is a image file
            is_image = False

            pattern_found = False
            for pattern in image_patterns:
                if url.find(pattern) != -1:
                    pattern_found = True
                    break

            if pattern_found:
                is_image = True
            else:
                continue
            '''if re.search(r"\.jpg\b|\.jpeg\b|\.jfif\b|\.pjpeg\b|\.pjp\b|\.png\b", url):
                #if re.search(r"\.jpg$|\.jpeg$|\.jfif$|\.pjpeg$|\.pjp$|\.png$", url):
                is_image = True
            else:
                continue'''

            # step 2: check the url contains the name
            has_name = False
            for name_part in name.split():
                if len(name_part) <= 2:
                    continue

                if name_part.lower() in url.lower():
                    has_name = True
                    break

            # step 4: return the final match result
            if is_image & has_name:
                clean_urls.append(url)

            else:
                is_detected = False
                detected_image_link = None

        if len(clean_urls) == 1:
            is_detected = True
            return is_detected, clean_urls[0]
        else:
            ##clean urls further
            for url in clean_urls:
                if url.find('http') != -1:
                    is_detected = True
                    detected_image_link = url
                    return is_detected, detected_image_link

        return is_detected, detected_image_link
