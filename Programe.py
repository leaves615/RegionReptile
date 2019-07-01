# coding=UTF-8

from RegionReptile import RegionReptile
import pypinyin

if __name__ == '__main__':
    reptile = RegionReptile()
    reptile.reptile_region('http://www.mca.gov.cn/article/sj/xzqh/2019/201901-06/201906211048.html')
    reptile.save_region('F:/Test/region_detail_location.json')
