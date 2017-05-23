from port.mod_jobs.business.JobData import JobData
from port.mod_jobs.business.DataKeeper import DataKeeper
import json
import requests
from requests.exceptions import RequestException
import re
from datetime import date,timedelta
import codecs
import sys
from port.mod_jobs.utils import convertCurrency


reload(sys)
sys.setdefaultencoding("utf-8")

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class JobCrawler(object):
    def __init__(self, keyword='', country=''):
        self.keyword=keyword
        self.country=country
        self.dk=DataKeeper(keyword=keyword,country=country)
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'X-Compress': '1',
            'Connection': 'keep-alive',
        }

    def Start(self):
        # Abstract method
        raise NotImplementedError
    
    def pv(self, expression, text, n=1):
        ret=[]
        m = re.search(expression, text)
        if m==None:
            ret.append('')
            return ret
        for x in xrange(n):
            ret.append(m.group(x+1))
        return ret

    def GetPage(self, host, lnk):
        #self.headers['Host']=host
        proxyError=False
        ret=''
        s = requests.Session()
        s.headers=self.headers
        try:
            r=s.get(lnk, verify=False)
            ex=r.status_code
        except RequestException as e:
            ex=e
            proxyError=True
        if(not proxyError and r!=None and r.status_code == requests.codes.ok):
            ret=r.text
        return ret
    
    def GetFile(self, host):
        with codecs.open("%s.html" % host, "r", "utf-8") as f:
            ret = f.read()
        return ret    
    
    def SaveFile(self, name, html):
        with codecs.open(name,'w',encoding='utf8') as f:
            f.write(html)

    def ParseSalary(self, txt, ishdr=False):
        salary0=''
        salary1=''
        period='day'
        txt=re.sub(r'(\d+)(k|K)', r'\1,000',txt)
        txt=txt.replace(',','').replace('.00','').replace('$','').replace('&#x27;','')
        v = self.pv(r'(\d+) ?- ?(\d+)', txt, 2)
        if len(v)==2:
            salary0,salary1=v
        if salary0=='':
            v = self.pv(r'(\d+) to (\d+)', txt, 2)
            if len(v)==2:
                salary0,salary1=v
        if salary0=='':
            v = self.pv(r'(\d+)', txt)
            if len(v)==1:
                salary0=v[0]
                salary1=salary0
        if salary0!='':
            if int(salary1)/int(salary0)>100:
                salary0=salary0+'000'
            usd0,usd1=convertCurrency(self.currency, salary0, salary1)
            if usd0<100:
                if ishdr:
                    return ['', '', '']
                period='hour'
            elif usd0>10000:
                period='annum'
            elif usd0>1000:
                period='month'
        return [salary0, salary1, period]