from pony import orm
from port.mod_ccm.models import *
from datetime import date,timedelta,datetime
from port.mod_jobs.business.JobCrawler import JobCrawler
import json
import requests
from requests.exceptions import RequestException
import re
from datetime import date,timedelta
import codecs
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class WTMCrawler(JobCrawler):
    def __init__(self, keyword=''):
        return super(WTMCrawler, self).__init__(keyword=keyword, country='WTM')

    

    def Start(self):
        self.snames={"Nicehash-NeoScrypt" : "NH-NS","Nicehash-Lyra2REv2" : "NH-Lyra","Nicehash-Blake (2b)" : "NH-B2b",
            "Nicehash-Blake (14r)" : "NH-B14r","Nicehash-CryptoNight" : "NH-CN","Nicehash-Pascal" : "NH-P",
            "Nicehash-LBRY" : "NH-LBRY","Nicehash-X11Gost" : "NH-X11","Nicehash-Ethash" : "NH-Et",
            "Nicehash-Equihash" : "NH-Eq",  }
        curdate=date.today()
        #curdate=date.today()-timedelta(days=1)
        with orm.db_session:
            gpus=GPU.select()[:]
        for gpu in gpus:
            self.GetGPU(gpu,curdate,islocal=True,issave=True)
        return '%d total, %d declined' % (self.dk.total,self.dk.declined)

    def GetGPU(self, gpu, curdate, islocal=False, issave=False): 
        host='whattomine.com'
        if islocal:
            html=self.GetFile(host+gpu.name)
        else:
            html=self.GetPage(host, gpu.link)
            if issave:
                self.SaveFile('%s%s.html'%(host,gpu.name), html)
        html=re.sub(r'(<tr class=[^>]*>)', '<tr >',html)
        html=re.sub(r'(</?a[^>]*>)', '',html)
        blockstart='<tr >'
        s=self.pv(r'alt="Btclogo" />([^<]+)', html)[0].strip().replace('$','').replace(',','')
        erbtcusd=float(s)
        with orm.db_session:
            btccurrency=Currency.get(sname='BTC')
            if btccurrency==None:
                btccurrency=Currency(name='Bitcoin',sname='BTC',isnh=False)
            exr=ExchangeRate.get(currency=btccurrency,dt=curdate)
            if exr==None:
                exr=ExchangeRate(currency=btccurrency,dt=curdate,exrbtc=1,exrusd=erbtcusd)
        parts=html.split(blockstart)
        for part in parts:
            if '<!DOCTYPE html>' in part:
                continue
            blocks=part.split('</td>')
            sname=''
            names = self.pv(r'<div style="margin-left: 50px">([^<]+)</div>\s*<div style="margin-left: 50px">([^<]+)', blocks[0],2)
            name0=names[0].strip()
            isNicehash=False
            if name0 in self.snames:
                name=name0
                sname=self.snames[name0]
                isNicehash=True
            elif '(' in name0:
                p=name0.split('(')
                name=p[0]
                sname=p[1][:-1]
            else:
                name=name0
            algorythm=names[1].strip()
            s=self.pv(r'<br>([^<]+)', blocks[3])[0].strip().replace(',','')
            rew24 = float(s)
            s=self.pv(r'<div class="text-center">([^<]+)', blocks[4])[0].strip()
            erbtc = float(s)
            #$([^<]+)<br>\s*<strong>\s*$([^<]+)
            parts=self.pv(r'<td>\s*([^<]+)<br>\s*<strong>\s*([^<]+)', blocks[7],2)
            cost0=float(parts[0].replace('$',''))
            cost1=float(parts[1].replace('$',''))
            powercost=cost0-cost1
            rew24btc = rew24*erbtc
            rew24usd = cost1 if isNicehash else rew24btc*erbtcusd-powercost
            with orm.db_session:
                curr=Currency.get(name=name)
                if curr==None:
                    curr=Currency(name=name,sname=sname,isnh=isNicehash)
                exr=ExchangeRate.get(currency=curr,dt=curdate)
                if exr==None:
                    exr=ExchangeRate(currency=curr,dt=curdate,exrbtc=erbtc,exrusd=erbtc*erbtcusd)
                resource=Resource.get(currency=curr,algorythm=algorythm,gpu=gpu.name,dt=curdate)
                if resource==None:
                    resource=Resource(currency=curr,algorythm=algorythm,gpu=gpu.name,rew24=rew24,rewbtc24=rew24btc,rewusd24=rew24usd,energy=powercost,dt=curdate)




    

