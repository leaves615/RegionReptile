# coding=UTF-8

from selenium import webdriver
from urllib import parse
import json
import requests


class RegionReptile(object):
    """区域信息爬虫"""

    def __init__(self):
        """初始化"""
        self.provincials = []
        self.region_details = dict()
        self.options = webdriver.ChromeOptions()
        # 设置浏览器无界面模式
        self.options.add_argument('--headless')

    def init_provincial(self):
        """解析省级信息JSON"""

        chrome = webdriver.Chrome(chrome_options=self.options)
        chrome.get('http://xzqh.mca.gov.cn/map')

        # 获取页面中的省级数据
        text = chrome.execute_script('return json')

        for item in text:
            provincial = dict()

            # 获取省级code
            provincial['code'] = int(item['quHuaDaiMa'])
            # 获取省级Name并解析出缩写数据
            temp = item['shengji'].replace(')', '')
            temp = temp.split('(')
            provincial['name'] = temp[0]
            provincial['abbr'] = temp[1]

            # 添加省级数据
            self.provincials.append(provincial)

            print(provincial)

        chrome.close()
        chrome.quit()

    def init_regions(self, url):
        """解析所有区划code和name"""

        chrome = webdriver.Chrome(chrome_options=self.options)
        chrome.get(url)

        # 获取大于三的tr标签
        trs = chrome.find_elements_by_xpath('/html/body/div/table/tbody/tr[position()>3]')

        for tr in trs:
            tds = tr.find_elements_by_tag_name('td')

            if tds[1].text != '':
                region_detail = dict()
                region_detail['code'] = int(tds[1].text)
                region_detail['name'] = tds[2].text
                region_detail['parent_name'] = None
                region_detail['parent_code'] = None
                region_detail['level'] = None
                region_detail['lon'] = None
                region_detail['lat'] = None
                region_detail['pinyin'] = None
                region_detail['abbrev'] = None

                self.region_details[region_detail['code']] = region_detail

                print(region_detail)
            else:
                break

        chrome.close()
        chrome.quit()

    def reptile_region_pinyin(self):
        """解析拼音数据"""

        chrome = webdriver.Chrome(chrome_options=self.options)
        chrome.get('http://xzqh.mca.gov.cn/map')

        region_value = chrome.find_element_by_id('pyArr').get_attribute('value')
        region_json = json.loads(region_value)

        for item in region_json:
            region_detail = self.region_details[int(item['code'])]

            if region_detail is not None:
                region_detail['pinyin'] = item['py']
                region_detail['abbrev'] = item['jp']

                print(region_detail)
            else:
                print(item)

        chrome.close()
        chrome.quit()

    def reptile_region_structure(self, provincial_code, provincial_name, provincial_abbr):
        """爬取区划等级结构信息"""

        # 拼接省级页面url
        url = 'http://xzqh.mca.gov.cn/defaultQuery?shengji='
        url += parse.quote((provincial_name + "(" + provincial_abbr + ")").encode("gb2312"))
        url += '&diji=-1&xianji=-1'

        chrome = webdriver.Chrome(chrome_options=self.options)
        chrome.get(url)

        # 获取行政区域列表
        trs = chrome.find_elements_by_xpath('//*[@id="center"]/div[3]/table/tbody/tr[position()>1]')

        # 临时信息 用于存储市级区域信息
        temp_region = dict()

        for tr in trs:

            # 获取信息列表
            tds = tr.find_elements_by_tag_name('td')

            # 解析code信息
            code = tds[4].get_attribute('textContent')

            # 判断是否为直辖 直辖跳过 非直辖记录信息
            if code == '' or code == str(provincial_code):
                continue

            region_detail = self.region_details[int(code)]

            # 判断市级节点和区县级节点
            if tr.get_attribute('class') == 'shi_nub':
                # 获取市级名称
                name = tds[0].find_element_by_tag_name('input').get_attribute('value')

                parent_name = provincial_name
                parent_code = provincial_code
                region_detail['level'] = 2

                temp_region[region_detail['name']] = region_detail['code']

            else:
                try:
                    # 不能获取直接跳过；跳过无具体信息的节点
                    parent_name = tds[0].find_element_by_tag_name('input').get_attribute('value')
                except:
                    continue

                parent_code = None
                if parent_name in temp_region:
                    parent_code = temp_region[parent_name]

                if parent_code is None:
                    parent_name = provincial_name
                    parent_code = provincial_code

                # 获取并存储区域名称
                region_detail['name'] = tds[0].get_attribute('textContent')
                region_detail['level'] = 3

            if parent_code != region_detail['code']:
                region_detail['parent_name'] = parent_name
                region_detail['parent_code'] = parent_code

            print(region_detail)

        chrome.close()
        chrome.quit()

    @staticmethod
    def reptile_region_location(search_name):
        """爬取行政区划地理位置信息"""
        url = 'https://apis.map.qq.com/jsapi?qt=poi&wd=' + search_name

        try:
            result = requests.get(url)
            if result.status_code == 200:
                result_json = result.json()

                # 判断是否获取
                if result_json['detail'] is not None and result_json['detail']['area'] is not None:
                    area = result_json['detail']['area']
                    location = dict()
                    location['name'] = area['cname']
                    location['code'] = area['acode']
                    location['lon'] = area['pointx']
                    location['lat'] = area['pointy']

                    return location
        except:
            print(search_name + " No Result")

        return None

    def reptile_region(self, url):
        """爬取省级市级和区县级数据"""

        print('========== 初始化省级数据 ==========')
        self.init_provincial()

        print()
        print('========== 初始化区划数据 ==========')
        self.init_regions(url)

        print()
        print('========== 解析拼音数据 ==========')
        self.reptile_region_pinyin()

        print()
        print('========== 解析区划结构 ==========')
        for item in self.provincials:
            region_detail = self.region_details[item['code']]
            region_detail['level'] = 1
            print(region_detail)
            self.reptile_region_structure(item['code'], item['name'], item['abbr'])
            print()

        print()
        print('========== 解析区划经纬度 ==========')
        # 获取经纬度信息
        for item in self.region_details.values():

            if item['parent_name'] is not None:
                search_name = item['parent_name']
            else:
                search_name = ''

            search_name += item['name']
            location = self.reptile_region_location(search_name)

            # 对比code信息，若为直辖市code结尾为9900
            if location is not None and (
                    location['code'] == item['code'] or (location['code'] - item['code']) == 9900):
                lon = location['lon']
                lat = location['lat']

                if lon is not None and lon != '':
                    item['lon'] = float(lon)

                if lat is not None and lat != '':
                    item['lat'] = float(lat)
                print(item)
            else:
                print(str(item['code']) + "\t" + item['name'])

    def save_region(self, path):
        """保存数据"""

        file = open(path, 'w')
        file.write(json.dumps(list(self.region_details.values()), ensure_ascii=False))
        file.flush()
        file.close()
