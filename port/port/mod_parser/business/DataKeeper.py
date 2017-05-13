import os
from pony import orm
from port.mod_parser.models import *

class DataKeeper: 
    def __init__(self, keyword='', country=''):
        self.items=[]
        self.keyword=keyword
        self.country=country
        self.declined=0
        self.total=0
        self.stat=dict()

    def AddItem(self, item):
        if not any(x.title == item.title and x.company == item.company and x.minsalary == item.minsalary for x in self.items):
            self.items.append(item)
            self.total+=1
            if item.service in self.stat:
                self.stat[item.service]+=1
            else:
                self.stat[item.service]=0
        else:
            self.declined+=1

    def AddItems(self, items):
        for x in items:
            self.AddItem(x)
    
    def RangeItems(self, days=3, total=0):
        dt=datetime.now()
        annumstat=self.rangeportion('annum')
        daystat=self.rangeportion('day')
        hourstat=self.rangeportion('hour')
        with orm.db_session:
            Log.select(lambda p: p.keyword==self.keyword and p.country==self.country).delete(bulk=True)
            log = Log(keyword=self.keyword, dt=dt,country=self.country)
            if annumstat!=None:
                res = Stat(keyword=self.keyword,country=self.country,days=days,total=total, dt=dt,period='annum',
                        startmin=annumstat['start_minvalue'],startmax=annumstat['start_maxvalue'],startavg=annumstat['start_avgvalue'],
                        topmin=annumstat['top_minvalue'],topmax=annumstat['top_maxvalue'],topavg=annumstat['top_avgvalue'],
                        vacancies=annumstat['vacancies'],applicants=annumstat['applicants'])
            if daystat!=None:
                res = Stat(keyword=self.keyword,country=self.country,days=days,total=total, dt=dt,period='day',
                        startmin=daystat['start_minvalue'],startmax=daystat['start_maxvalue'],startavg=daystat['start_avgvalue'],
                        topmin=daystat['top_minvalue'],topmax=daystat['top_maxvalue'],topavg=daystat['top_avgvalue'],
                        vacancies=daystat['vacancies'],applicants=daystat['applicants'])
            if hourstat!=None:
                res = Stat(keyword=self.keyword,country=self.country,days=days,total=total, dt=dt,period='hour',
                        startmin=hourstat['start_minvalue'],startmax=hourstat['start_maxvalue'],startavg=hourstat['start_avgvalue'],
                        topmin=hourstat['top_minvalue'],topmax=hourstat['top_maxvalue'],topavg=hourstat['top_avgvalue'],
                        vacancies=hourstat['vacancies'],applicants=hourstat['applicants'])
            JobEntity.select(lambda p: p.keyword==self.keyword and p.country==self.country).delete(bulk=True)
            for x in self.items:
                item = JobEntity(keyword=self.keyword,country=self.country,service=x.service,link=x.link,title=x.title,dt=x.date,
                                 website=x.website,company=x.company,location=x.location,time=x.time,jobtype=x.jobtype,currency=x.currency,
                                 minsalary=int(float(x.minsalary)),maxsalary=int(float(x.maxsalary)),minusdsalary=x.minusd,maxusdsalary=x.maxusd,
                                 startrange=x.minrange,toprange=x.maxrange,period=x.period,applicants=x.applicants,description=x.description)
        self.items=[]

    def rangeportion(self,filter):
        portion = [item for item in self.items if item.period == filter]
        if len(portion)==0:
            return
        if len(portion)==1:
            portion[0].minrange=2
            portion[0].maxrange=2
            return
        l=len(portion)
        applicants=sum(item.applicants for item in portion)
        start_minvalue=min(item.minusd for item in portion)
        start_maxvalue=max(item.minusd for item in portion)
        start_avgvalue=sum(item.minusd for item in portion)/l
        mir=(start_avgvalue-start_minvalue)/5
        mar=(start_maxvalue-start_avgvalue)/5
        rangemin=[start_minvalue+mir*2,start_minvalue+mir*4,start_maxvalue-mar*4,start_maxvalue-mar*2]
        top_minvalue=min(item.maxusd for item in portion)
        top_maxvalue=max(item.maxusd for item in portion)
        top_avgvalue=sum(item.maxusd for item in portion)/l
        mir=(top_avgvalue-top_minvalue)/5
        mar=(top_maxvalue-top_avgvalue)/5
        rangemax=[top_minvalue+mir*2,top_minvalue+mir*4,top_maxvalue-mar*4,top_maxvalue-mar*2]
        for x in portion:
            if x.minusd<rangemin[0]:
                x.minrange=0
            elif x.minusd<rangemin[1]:
                x.minrange=1
            elif x.minusd<rangemin[2]:
                x.minrange=2
            elif x.minusd<rangemin[3]:
                x.minrange=3
            else:
                x.minrange=4
            if x.maxusd<rangemax[0]:
                x.maxrange=0
            elif x.maxusd<rangemax[1]:
                x.maxrange=1
            elif x.maxusd<rangemax[2]:
                x.maxrange=2
            elif x.maxusd<rangemax[3]:
                x.maxrange=3
            else:
                x.maxrange=4
        return { 'start_minvalue' : start_minvalue,'start_maxvalue' : start_maxvalue,'start_avgvalue' : start_avgvalue,
                'top_minvalue' : top_minvalue,'top_maxvalue' : top_maxvalue,'top_avgvalue' : top_avgvalue,
                'vacancies' : l,'applicants' : applicants }
