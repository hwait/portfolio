from port.mod_parser.business.JobData import JobData
from port.mod_parser.business.DataKeeper import DataKeeper
from port.mod_parser.business.JobCrawler import JobCrawler
import json
import requests
from requests.exceptions import RequestException
import re
from datetime import date,timedelta
import codecs
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class AUSCrawler(JobCrawler):
    def __init__(self, keyword=''):
        return super(AUSCrawler, self).__init__(keyword=keyword, country='AUS')

    def Start(self):
        self.currency='AU$'
        self.total=0
        self.GetSeek(islocal=True,issave=True)
        self.dk.AddItems(self.ParseAdzuna(islocal=True,issave=True))
        self.dk.RangeItems(days=2, total=self.total)
        return '%d total, %d declined' % (self.dk.total,self.dk.declined)

    def GetSeek(self, islocal=False, issave=False): 
        self.stopflag=False
        c=1
        while not self.stopflag:
            self.dk.AddItems(self.ParseSeek(c,islocal=islocal,issave=issave))
            c+=1

    def ParseSeek(self, n, islocal=False, issave=False): 
        host='www.seek.com.au'
        if islocal:
            html=self.GetFile(host+str(n))
        else:
            html=self.GetPage(host, 'https://www.seek.com.au/%s-jobs?daterange=3&page=%d&sortmode=ListedDate' % (self.keyword, n))
            if issave:
                self.SaveFile('%s%s.html'%(host,n), html)
        blockstart='<article '
        blockend='</article>'
        jobs=[]
        parts=html.split(blockstart)
        for block in parts:
            if '<html lang="en">' in block:
                continue
            self.total+=1
            block=block[:block.find(blockend)]
            title = self.pv(r'aria-label="([^"]+)', block)[0]
            link = self.pv(r'"url":"([^"]+)', block)[0]
            if ' hours ago' in block:
                ds = date.today()
            elif 'one day ago' in block:
                ds = date.today()-timedelta(days=1)
            elif 'two days ago' in block:
                self.stopflag=True
                return jobs
            company=self.pv(r'<span data-automation="jobAdvertiser" data-reactid="\d+">([^<]+)', block)[0]
            timetext=self.pv(r'This is a <!-- /react-text --><!-- react-text: \d+ -->([^<]+)', block)[0]
            if 'Temp' in timetext:
                time='part-time'
            else:
                time='full-time'
            if 'Contract' in timetext:
                jobtype='Contract'
            elif 'Temp' in timetext:
                jobtype='Temporary'
            else:
                jobtype='Permanent'
            salarytext=self.pv(r'aria-label="Salary: ([^"]+)', block)[0]
            salary0,salary1,period=self.ParseSalary(salarytext)
            if salary0=='':
                salary0,salary1,period=self.ParseSalary(title)
            if salary0=='' or int(salary0)<10:
                continue

            applicants=0
            website=' '           
            bs='</p></span>'
            be='<div class="_6sZH95V"'
            start_pos=block.find(bs)
            end_pos=block.find(be)
            part=block[start_pos+11:end_pos]
            part=re.sub(r'(</?span[^>]*>)', '',part)
            part=re.sub(r'(<ul[^>]*>)', '<ul>',part)
            part=re.sub(r'(<li[^>]*>)', '<li>',part)
            part=re.sub(r'(<p[^>]*>)', '<p>',part)
            description=part
            location=self.pv(r'"addressRegion":"([^"]+)', block)[0]
            data=JobData(host,link,title,ds,website,company,location,time,jobtype,self.currency,salary0,salary1,period,applicants,description)
            jobs.append(data)
        return jobs

    def ParseAdzuna(self, islocal=False, issave=False): 
        host='www.adzuna.com.au' # Single page only 
        if islocal:
            html=self.GetFile(host)
        else:
            html=self.GetPage(host, 'https://www.adzuna.com.au/search?f=3&loc=105392&pp=50&sb=date&sd=down&q=%s' % self.keyword)
            if issave:
                self.SaveFile('%s.html'%host, html)
        blockstart='<h2><a'
        blockend='<a href="#" class="t_s">Share</a>'
        jobs=[]
        parts=html.split(blockstart)
        for block in parts:
            if '<html lang="en-AU">' in block:
                continue
            self.total+=1
            block=block[:block.find(blockend)]
            title = self.pv(r'<span itemprop="title">([^<]+)', block)[0]
            link = self.pv(r'<a href="(https://www.adzuna.com.au/land/ad/\d+)', block)[0]
            if link=='':
                link = self.pv(r'href="(https://www.adzuna.com.au/details/[^"]+)', block)[0]
            location=company=self.pv(r'<span itemprop="addressLocality">([^<]+)', block)[0]
            salarytext=self.pv(r'<span itemprop="baseSalary" class="at_sl">([^<]+)', block)[0].replace(',','').replace('.00','').replace('AU$','').replace('AUD','')
            salary0,salary1,period=self.ParseSalary(salarytext)
            if salary0=='':
                salary0,salary1,period=self.ParseSalary(title)
            if salary0=='' or int(salary0)>500000:
                continue
            jobtype='Permanent'
            time='full-time'
            company=self.pv(r'<span itemprop="name">([^<]+)', block)[0]
            applicants=0
            website=' '
            ds = date.today()
            block=re.sub(r'(</?strong>)', '',block)
            description=self.pv(r'<span class="at_tr">([^<]+)', block)[0].strip().replace('&nbsp;',' ')
            data=JobData(host,link,title,ds,website,company,location,time,jobtype,self.currency,salary0,salary1,period,applicants,description)
            jobs.append(data)
        return jobs

    def ParseAdzunaPage(self, link): 
        host='www.adzuna.com.au'
        html=self.GetPage(host, link)
        parts=html.split('Apply for this job</a>')
        #parts=html.split('<a target="_blank"')
        if len(parts)<2:
            return ''
        part=parts[1]
        part=re.sub(r'(</?div[^>]*>)', '',part)
        part=part.replace('</p><h2>Description</h2>','').replace('<p>Salary comparison:</p>','').replace('<p><a','<a')
        part=re.sub(r'(<a[^>]*>)', '',part)
        return part

    def ParseSeekPage(self, link): 
        host='www.seek.com.au'
        html=self.GetPage(host, link)
        bs='<div id="jobTemplate">'
        be='<!-- START: Apply section below template -->'
        start_pos=html.find(bs)
        end_pos=html.find(be)
        part=html[start_pos:end_pos].replace('<!--','').replace('-->','').replace('<p>&nbsp;</p>','').replace('<img src="','<img src="https://%s'%host)
        part=re.sub(r'(</?div[^>]*>)', '',part)
        part=re.sub(r'(</?blockquote[^>]*>)', '',part)
        part=re.sub(r'(<style[^>]*>[^<]+</style>)', '',part)
        part=re.sub(r'(<TABLE[^>]*>)', '<TABLE>',part).strip()
        return part
