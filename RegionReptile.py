# coding=UTF-8

from selenium import webdriver
from urllib import parse
import json
import requests


class RegionModel(object):
    """区域信息模型"""

    def __init__(self, code, name):
        """初始化"""
        self.code = code
        self.name = name
        self.parent_code = None
        self.parent_name = None
        self.level = None
        self.longitude = None
        self.latitude = None
        self.pinyin = None
        self.abbreviation = None

    def to_string(self):
        model_string = '{"code":' + str(self.code)
        model_string += ',"name":"' + str(self.name)
        model_string += ',"parent_code:"' + str(self.parent_code)
        model_string += ',"parent_name":"' + str(self.parent_name)
        model_string += ',"level":' + str(self.level)
        model_string += ',"longitude":' + str(self.longitude)
        model_string += ',"latitude":' + str(self.latitude)
        model_string += ',"pinyin":' + str(self.pinyin)
        model_string += ',"abbreviation":' + str(self.abbreviation)
        model_string += "}"
        return model_string


class RegionReptile(object):

    def __init__(self):
        """初始化"""
        # 存储区域信息
        self.region_list = []

        # 设置浏览器无界面模式
        self.__options = webdriver.ChromeOptions()
        self.__options.add_argument('--headless')

    def __get_region_by_code(self, code):
        """通过code获取行政列表"""
        for item in self.region_list:
            if item.code == code:
                return item

        return None

    def reptile_region_basic(self, url):
        """解析所有区划基础数据"""

        chrome = webdriver.Chrome(chrome_options=self.__options)
        chrome.get(url)

        # 获取大于三的tr标签
        trs = chrome.find_elements_by_xpath('/html/body/div/table/tbody/tr[position()>3]')

        # 解析每行tr标签
        for tr in trs:
            texts = tr.text.split(' ')

            if texts is not None and len(texts) >= 2:
                region_model = RegionModel(int(texts[0]), texts[1])
                self.region_list.append(region_model)

                print(region_model.to_string())
            else:
                break

        chrome.close()
        chrome.quit()

    def __init_provincial(self):
        """解析省级信息JSON"""

        chrome = webdriver.Chrome(chrome_options=self.__options)
        chrome.get('http://xzqh.mca.gov.cn/map')

        # 获取页面中的省级数据
        text = chrome.execute_script('return json')

        provincials = []
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
            provincials.append(provincial)

            print(provincial)

        chrome.close()
        chrome.quit()

        return provincials

    def __init_region_structure(self, provincial_code, provincial_name, provincial_abbr):
        """爬取单个省区划等级结构信息"""

        # 拼接省级页面url
        url = 'http://xzqh.mca.gov.cn/defaultQuery?shengji='
        url += parse.quote((provincial_name + "(" + provincial_abbr + ")").encode("gb2312"))
        url += '&diji=-1&xianji=-1'

        chrome = webdriver.Chrome(chrome_options=self.__options)
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

            region_model = self.__get_region_by_code(int(code))

            # 判断市级节点和区县级节点
            if tr.get_attribute('class') == 'shi_nub':
                parent_name = provincial_name
                parent_code = provincial_code
                region_model.level = 2

                temp_region[region_model.name] = region_model.code
            else:
                try:
                    # 不能获取直接跳过；跳过无具体信息的节点
                    parent_name = tds[0].find_element_by_tag_name('input').get_attribute('value')
                except:
                    continue

                if parent_name in temp_region:
                    parent_code = temp_region[parent_name]
                else:
                    parent_name = provincial_name
                    parent_code = provincial_code

                region_model.level = 3

            if parent_code != region_model.code:
                region_model.parent_name = parent_name
                region_model.parent_code = parent_code

            print(region_model.to_string())

        chrome.close()
        chrome.quit()

    def reptile_region_structure(self):
        """"爬取各个省区划等级结构信息"""

        provincials = self.__init_provincial()

        for item in provincials:
            region_model = self.__get_region_by_code(item['code'])
            region_model.level = 1
            print(region_model.to_string())
            self.__init_region_structure(item['code'], item['name'], item['abbr'])

    def reptile_region_pinyin(self):
        """解析拼音数据"""

        chrome = webdriver.Chrome(chrome_options=self.__options)
        chrome.get('http://xzqh.mca.gov.cn/map')

        region_value = chrome.find_element_by_id('pyArr').get_attribute('value')
        region_json = json.loads(region_value)

        for item in region_json:
            region_model = self.__get_region_by_code(int(item['code']))

            if region_model is not None:
                region_model.pinyin = item['py']
                region_model.abbreviation = item['jp']

                print(region_model.to_string())
            else:
                print(item)

        chrome.close()
        chrome.quit()

    def reptile_region_location(self):
        """爬取行政区划地理位置信息"""

        url = 'https://apis.map.qq.com/jsapi?qt=poi&wd='

        # 获取经纬度信息
        for item in self.region_list:

            if item.parent_name is not None:
                search_name = item.parent_name
            else:
                search_name = ''

            search_name += item.name

            try:
                result = requests.get(url + search_name)
                if result.status_code == 200:
                    result_json = result.json()

                    # 判断是否获取
                    if result_json['detail'] is not None and result_json['detail']['area'] is not None:
                        area = result_json['detail']['area']

                        # 对比code信息，若为直辖市code结尾为9900
                        if area['acode'] == item.code or area['acode'] - item.code:
                            if area['pointx'] is not None and area['pointx'] != '':
                                item.longitude = float(area['pointx'])
                            if area['pointy'] is not None and area['pointy'] != '':
                                item.latitude = float(area['pointy'])

                print(item.to_string())
            except:
                print(search_name + " No Result")
