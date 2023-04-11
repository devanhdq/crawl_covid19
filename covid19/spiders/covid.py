import scrapy
from scrapy_splash import SplashRequest
import re


class CovidSpider(scrapy.Spider):
    name = "covid"
    allowed_domains = ["covid19.gov.vn"]
    start_urls = [
        "https://covid19.gov.vn/big-story/cap-nhat-dien-bien-dich-covid-19-moi-nhat-hom-nay-171210901111435028.htm",
        "https://covid19.gov.vn/big-story/ca-nhat-dien-bien-dich-covid-19-171210901110957364.htm"
    ]
    lua_script = '''
        function main(splash)
          splash:go(splash.args.url)
          splash:wait(1)
          while splash:select("#loadmorebtn.loadmore") do
            local loadmorebtn = splash:select("#loadmorebtn.loadmore")
            if loadmorebtn then
              loadmorebtn:click()
              splash:wait(1)
            else
              break
            end
          end
          repeat
            local old_height = splash:evaljs("document.body.scrollHeight")
            splash:runjs("window.scrollTo(0, document.body.scrollHeight);")
            splash:wait(1)
            local new_height = splash:evaljs("document.body.scrollHeight")
            if new_height == old_height then
              break
            end
          until false
          return splash:html()
        end
    '''

    # hàm convert trường time theo định dạng hh-mm dd-mm-yyyy
    def reformat_date(self, date_string):
        from datetime import datetime
        date_object = datetime.strptime(date_string, "%H:%M %d/%m/%Y")
        return date_object.strftime("%H:%M %d-%m-%Y")

    #  hàm thay thế các chữ tiếng việt
    def no_accent_vietnamese(self, s):
        s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
        s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
        s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
        s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
        s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
        s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
        s = re.sub(r'[ìíịỉĩ]', 'i', s)
        s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
        s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
        s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
        s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
        s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
        s = re.sub(r'[Đ]', 'D', s)
        s = re.sub(r'[đ]', 'd', s)

        marks_list = [u'\u0300', u'\u0301', u'\u0302', u'\u0303', u'\u0306', u'\u0309', u'\u0323']

        for mark in marks_list:
            s = s.replace(mark, '')
        return s

    def handles_case(self, case_raw):
        regex = r'\d+\.\d+|\d+'

        case_raw = re.findall(regex, case_raw)
        if len(case_raw) > 0:
            case_raw = int(case_raw[0].replace('.', ''))
        return case_raw

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.parse,
                endpoint='execute',
                args={
                    'lua_source': self.lua_script,
                    "timeout": 3000
                },
            )

    def handle_detail(self, detail):
        regex = r'(\b[A-Z][\w\s]+\b)\s*\((\d+(?:\.\d+)?)\)\s*'
        result = []
        matches = re.findall(regex, detail)
        for match in matches:
            result.append({"city": match[0], "case": match[1]})
        return result

    def parse(self, response):
        total = response.css('.timeline-item')
        for item in total:
            time = item.css('.timeago').attrib['title']
            new_case = item.css('.item-bigstory-tit h3::text').get().strip()
            detail = item.css('.kbwscwl-content p:nth-child(2)::text').get()
            more_detail = item.css('.kbwscwl-content p:nth-child(1)::text').get()
            #
            # new_case = self.handles_case(new_case)
            # detail = self.handle_detail(detail)
            #
            # if (new_case == "" or detail == None):
            #     new_case = more_detail

            yield {
                "time": time,
                "new_case": new_case,
                "city_case": detail,
                "more_detail": more_detail
            }
