from port.mod_parser.utils import convertCurrency

class JobData:
    def __init__(self,host,link,title,date,website,company,location,time,jobtype,currency,minsalary,maxsalary,period,applicants,description):
        self.service=host
        self.link=link
        self.title=title
        self.date=date
        self.website=website
        self.company=company
        self.location=location
        self.time=time
        self.jobtype=jobtype
        self.currency=currency
        self.minsalary=minsalary
        self.maxsalary=maxsalary
        self.minrange=0
        self.maxrange=0
        self.period=period
        self.applicants=int(applicants)
        self.description=description
        self.Calculate()

    def Validate(self):
        if(self.data['city']!='' 
           and self.data['region']!='' 
           and self.data['link']!='' 
           and self.data['date']!='' 
           and self.data['salary0']!='' 
           and self.data['salary1']!='' 
           and self.data['company']!='' 
           and self.data['website']!='' 
           and self.data['applicants']!='' 
           and self.data['title']!='' 
           and self.data['description']!='' 
           and self.data['period']!='' 
           and self.data['type']!='' 
           and self.data['service']!='' 
           and self.data['time']!=''):
            return ''
        return '-'

    def Calculate(self):
        self.minusd,self.maxusd=convertCurrency(self.currency,self.minsalary,self.maxsalary)