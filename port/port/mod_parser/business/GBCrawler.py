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

class GBCrawler(JobCrawler):
    def __init__(self, keyword=''):
        return super(GBCrawler, self).__init__(keyword=keyword, country='GB')

    def Start(self):
        self.currency='&pound;'
        self.total=0
        self.GetReed(islocal=True,issave=True)
        self.GetCwjobs(islocal=True,issave=True)
        self.dk.RangeItems(days=2, total=self.total)
        return '%d total, %d declined' % (self.dk.total,self.dk.declined)
    
    def GetCwjobs(self, islocal=False, issave=False): 
        self.stopflag=False
        c=1
        while not self.stopflag:
            self.dk.AddItems(self.ParseCwjobs(c,islocal=islocal,issave=issave))
            c+=1

    def GetReed(self, islocal=False, issave=False): 
        self.pagemax=1
        self.dk.AddItems(self.ParseReed(1,islocal=islocal,issave=issave))
        for x in range(2,self.pagemax+1):
            self.dk.AddItems(self.ParseReed(x,islocal=islocal,issave=issave))

    def ParseCwjobs(self, n, islocal=False, issave=False): 
        host='www.cwjobs.co.uk'
        if islocal:
            html=self.GetFile(host+str(n))
        else:
            html=self.GetPage(host, 'https://www.cwjobs.co.uk/jobs/%s?Sort=2&page=%d' % (self.keyword, n))
            if issave:
                self.SaveFile('%s%s.html'%(host,n), html)
        blockstart='typeof="JobPosting"'
        blockend='<div class="discipline-related-links">'
        jobs=[]
        parts=html.split(blockstart)
        for block in parts:
            if '<html lang="en">' in block:
                continue
            self.total+=1
            block=block[:block.find(blockend)]
            title = self.pv(r'<meta property="title" content="([^"]+)" />', block)[0]
            link = self.pv(r'<meta property="url" content="([^"]+)" />', block)[0]
            bs='<span property="address" typeof="Postaladdress">'
            be='<li class="salary"'
            start_pos=block.find(bs)
            end_pos=block.find(be)
            part=block[start_pos:end_pos]
            location=re.sub(r'(<[^>]+>)', '',part).strip()
            salarytext=self.pv(r'<li class="salary" property="baseSalary" title="salary">([^<]+)</li>', block)[0]
            if '&#128;' in salarytext:
                self.currency='&euro;'
            elif '&#36;' in salarytext:
                self.currency='US$'
            salary0,salary1,period=self.ParseSalary(salarytext.replace('&#163;','').replace('&#128;','').replace('&#36;',''))
            if salary0=='':
                salary0,salary1,period=self.ParseSalary(title.replace('&#163;','').replace('&#128;','').replace('&#36;',''), ishdr=True)
            if salary0=='':
                continue
            jobtype=self.pv(r'<span property="employmentType" title="employment type">([^<]+)', block)[0]
            time='full-time'
            company=self.pv(r'<meta property="name" content="([^"]+)" />', block)[0]
            applicants=0
            website=' '
            v=self.pv(r'<span >([^<]+)</span>', block)[0].strip()
            if v=='Today':
                ds = date.today()
            elif v=='Yesterday':
                ds = date.today()-timedelta(days=1)
            if v=='Posted 2 days ago':
                self.stopflag=True
                return jobs
            block=re.sub(r'(</?span[^>]*>)', '',block).replace('<strong>','').replace('</strong>','')
            description=self.pv(r'<p class="job-intro">([^<]+)', block)[0].strip().replace('&hellip;','...').replace('&nbsp;',' ')
            data=JobData(host,link,title,ds,website,company,location,time,jobtype,self.currency,salary0,salary1,period,applicants,description)
            jobs.append(data)
        return jobs

    def ParseReed(self, n, islocal=False, issave=False): 
        host='reed.co.uk'
        if islocal:
            html=self.GetFile(host+str(n))
        else:
            html=self.GetPage(host, 'https://www.reed.co.uk/jobs/it-jobs?cached=True&pageno=%d&keywords=%s&datecreatedoffset=LastThreeDays' % (n, self.keyword))
            if issave:
                self.SaveFile('%s%s.html'%(host,n), html)
        #html=self.GetFile(host+str(n))
        bs='itemtype="https://schema.org/JobPosting">'
        be='</article>'
        jobs=[]
        #<span class="count ">([^<]+)</span>
        v = self.pv(r'<span class="count ">([^<]+)</span>', html)[0]
        self.pagemax=int(int(v)/25)
        for block in html.split(bs):
            end_pos=block.find(be)
            block=block[:end_pos]
            v = self.pv(r'<a href="/jobs/([^#]+)#/jobs/it-jobs\?keywords=[^"]+" data-id="\d+" itemprop="title" title="[^"]+" class="gtmJobTitleClickResponsive">([^<]+)</a>', block, 2)
            if v[0]=='':
                continue
            self.total+=1
            link ='https://reed.co.uk/jobs/%s' % v[0]
            title = v[1].replace('&#163;','&pound;').replace('\xe2\x82\xac','&euro;').replace('\xc2\xa3','&pound;')
            v = self.pv(r'Posted ([^<]+)<a href="([^"]+)" class="[^"]+">([^<]+)</a>', block, 3)
            if v[0]=='Today by ':
                ds = date.today()
            elif v[0]=='Yesterday by ':
                ds = date.today()-timedelta(days=1)
            elif v[0]=='2 days ago by ':
                ds = date.today()-timedelta(days=2)
            #elif v[0]=='3 days ago by ':
            #    ds = date.today()-timedelta(days=3)
            else:
                continue
            website ='https://reed.co.uk%s' % v[1]
            company = v[2]
            location = self.pv(r'<li class="location">([^<]+)</li>', block)[0]
            type,time = self.pv(r'<li class="time">([^<]+)</li>', block)[0].split(',')
            salarytext = self.pv(r'<li class="salary">([^<]+)</li>', block)[0].replace('&#163;','').replace('\xc2\xa3','&pound;')
            self.currency='&pound;'
            if '\xe2\x82\xac' in salarytext:
                self.currency='&euro;'
            elif 'USD$' in salarytext:
                self.currency='US$'
            salarytext=salarytext.replace('\xe2\x82\xac','').replace('USD$','')
            salary0,salary1,period=self.ParseSalary(salarytext)
            if salary0=='':
                salary0,salary1,period=self.ParseSalary(title, ishdr=True)
            if salary0=='':
                continue
            applicants = self.pv(r'<li class="applications">(\d+) applications?</li>', block)[0]
            bs='<div class="description hidden-xs" itemprop="description">'
            es='</div>'
            sp=block.find(bs)
            ep=block.find(es,sp)
            description=block[sp+60:ep].replace('<span class="highlight">','').replace('</span>','').replace('\xe2\x82\xac','&euro;').replace('\xc2\xa3','&pound;')
            data=JobData(host,link,title,ds,website,company,location,time,type, self.currency,salary0,salary1,period,applicants,description)
            jobs.append(data)
        return jobs


    
    def ParseCwjobsPage(self, link): 
        host='www.cwjobs.co.uk'
        html=self.GetPage(host, link)
        bs='<div class="job-description">'
        be='<ul class="contact-reference hidden-xs">'
        start_pos=html.find(bs)
        end_pos=html.find(be)
        part=html[start_pos:end_pos].replace(' property="experienceRequirements"','').replace('<div class="job-description">','')
        part=re.sub(r'(</?span[^>]*>)', '',part).strip()
        return part

    def ParseReedPage(self, link): 
        host='reed.co.uk'
        html=self.GetPage(host, link)
        bs='<div class="description" itemprop="description">'
        be='<div class="application-box">'
        start_pos=html.find(bs)
        end_pos=html.find(be)
        part=html[start_pos:end_pos].replace('unstyled-list ','').replace('<div class="skills">','').replace('lozenge ','')
        part=re.sub(r'(</?div[^>]*>)', '',part)
        part=re.sub(r'(<button[^>]*>[^<]+</button>)', '',part).strip()
        return part