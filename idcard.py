# -*- coding: utf-8 -*-
import scrapy,requests,json,copy
from scrapy_idcard_5108.common.function import *
from scrapy_idcard_5108.items import Idcard5108Item

class Idcard5108Spider(scrapy.Spider):
    name = 'idcard_5108'
    
    start_urls = ['http://xx.xx.xx.xx:8000/login/']
    #post发起登录请求
    def parse(self, response):
        url_login = 'http://xx.xx.xx.xx:8000/login'
        headers = {#略去          
        }
        post_data = {'username':' ',
                'password':' '
        }
        yield scrapy.FormRequest(url_login,formdata=post_data,callback=self.parse_after)

    def parse_after(self,response):
        query_url = 'http://xx.xx.xx.xx:8000/jbxx/jbxxCzrkSimpleQueryAndLockListData'
        # 生成6位地址码
        qxcode_list = input('请输入县区号：如510824  ')
        qxcode_lists = [qxcode_list]
        for index in range(len(qxcode_lists)):
            qxcode = qxcode_lists[index]
            # 生成8位出生年月日（生日）例：19920318
            for year in range(1954,2006):
                for months in range(1,13):
                    if int(months)<10 :
                        month = '0' + str(months)
                    else:
                        month = str(months)
                    days_dic = {'01':31,'02':29,'03':31,'04':30,'05':31,'06':30,'07':31,'08':31,'09':30,'10':31,'11':30,'12':31}
                    days = days_dic[month]
                    for day in range(1,int(days)+1):
                        if int(day)<10 :
                            day = '0' + str(day)
                        else:
                            day = str(day)
                        birthday = str(year) + month + day
                        # 生成三位顺序码，尾数偶数为男性，奇数为女性
                        for order in range(1,1000):
                            id_order = ''
                            if int(order)>= 100:
                                id_order = str(order)
                            elif int(order) >= 10:
                                id_order = '0' + str(order)
                            else:
                                id_order = '00' + str(order)
                            idcard17 = str(qxcode) + str(birthday) + str(id_order)
                            # print('17位身份证编码为：{}'.format(idcard17))
                            count = 0
                            weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2] #权重项
                            checkcode ={'0':'1','1':'0','2':'X','3':'9','4':'8','5':'7','6':'6','7':'5','8':'4','9':'3','10':'2'} #校验码映射
                            for i in range(0,len(idcard17)):
                                count = count +int(idcard17[i])*weight[i]
                            idcard = idcard17 + checkcode[str(count%11)] #算出校验码
                            #print('18位身份证编码为：{0} 验证码 {1}'.format(idcard,is_valid_idcard(idcard)))
                            value = '{"oredCriteria":[[{"property":"gmsfhm","operator":"=","value":"'+str(idcard)+'","datatype":"0"},{"property":"pcs","operator":">=","value":"510800000000","datatype":"0"},{"property":"pcs","operator":"<=","value":"510899999999","datatype":"0"}]],"pager":{"start":0,"limit":20,"pageSize":20}}'
                            data = {'txtQuery':value,'txtXmMh':'','bzw':'000001'}
                            yield scrapy.FormRequest(query_url,formdata=data,meta={'gmsfhm':str(idcard)},callback=self.parse_detail)
    #获取身份证相关字段数据
    def parse_detail(self,response):
        gmsfhm = copy.copy(response.meta.get('gmsfhm',''))
        page_dic = json.loads(response.body.decode())
        totalRecord = page_dic["totalRecords"]
        if totalRecord==0:
            print('{0} 查询无记录'.format(gmsfhm))
        else:
            print('{0} 查询成功'.format(gmsfhm))
            xm = page_dic["data"][0]["xm"]
            gmsfhm = page_dic["data"][0]["gmsfhm"]
            rkbm = page_dic["data"][0]["rkbm"]
            lxdh = page_dic["data"][0]["lxdh"]
            # print('{0} {1} {2}'.format(xm,gmsfhm,rkbm,lxdh))
            headers={}
            image_index = 'http://xx.xx.xx.xx:8000/jbxx/jbxxXpDetail?rkbm=' + rkbm
            yield scrapy.Request(url=image_index,meta={'xm':xm,'gmsfhm':gmsfhm,'rkbm':rkbm,'lxdh':lxdh},headers=headers,callback=self.image_bh)
    #通过response得到image_url，并发起图片下载和字段处理
    def image_bh(self,response):
        image_url = 'http://xx.xx.xx.xx:8000' + response.xpath('//ul[@id="pictureGroup"]//img/@src').extract_first('')
        xm = copy.copy(response.meta.get('xm',''))
        gmsfhm = copy.copy(response.meta.get('gmsfhm',''))
        rkbm = copy.copy(response.meta.get('rkbm',''))
        lxdh = copy.copy(response.meta.get('lxdh',''))
        idcard_item = Idcard5108Item()
        idcard_item['xm'] = xm
        idcard_item['gmsfhm'] = gmsfhm
        idcard_item['rkbm'] = rkbm
        idcard_item['lxdh'] = lxdh
        idcard_item['image_url'] = [image_url]#获取图片
        yield idcard_item
