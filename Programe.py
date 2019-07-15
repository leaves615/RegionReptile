# coding=UTF-8
from RegionReptile import RegionReptile

if __name__ == '__main__':
    reptile = RegionReptile()

    print()
    print('========== 解析基础数据 ==========')
    reptile.reptile_region_basic('http://www.mca.gov.cn/article/sj/xzqh/2019/201901-06/201906211048.html')

    print()
    print('========== 解析拼音数据 ==========')
    reptile.reptile_region_pinyin()

    print()
    print('========== 解析区划结构 ==========')
    reptile.reptile_region_structure()

    print()
    print('========== 解析区划经纬度 ==========')
    reptile.reptile_region_location()

    file = open('F:/Test/region_detail_location.json', 'w')
    for item in reptile.region_list:
        file.write(item.to_string())
        file.flush()
    file.close()
