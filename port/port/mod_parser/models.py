from pony import orm
from datetime import datetime, date
from port.mod_parser.utils import convertCurrency

db = orm.Database()

class Log(db.Entity):
    _table_ = 'Logs'
    keyword = orm.Required(str)
    country = orm.Required(str)
    dt = orm.Required(datetime)

class Stat(db.Entity):
    _table_ = 'Stats'
    country = orm.Required(str)
    keyword = orm.Required(str)
    period=orm.Required(str)
    dt = orm.Required(datetime)
    startmin=orm.Required(int)
    startavg=orm.Required(int)
    startmax=orm.Required(int)
    topmin=orm.Required(int)
    topavg=orm.Required(int)
    topmax=orm.Required(int)
    applicants=orm.Required(int)
    vacancies=orm.Required(int)
    total=orm.Required(int)
    days=orm.Required(int)


class JobEntity(db.Entity):
    _table_ = 'Jobs'
    keyword=orm.Required(str)
    country=orm.Required(str)
    service=orm.Required(str)
    link=orm.Required(str)
    title=orm.Required(str)
    dt=orm.Required(date)
    website=orm.Optional(str)
    company=orm.Optional(str)
    location=orm.Required(str)
    time=orm.Required(str)
    jobtype=orm.Required(str)
    currency=orm.Required(str)
    minsalary=orm.Required(int)
    maxsalary=orm.Required(int)
    minusdsalary=orm.Required(int)
    maxusdsalary=orm.Required(int)
    startrange=orm.Required(int)
    toprange=orm.Required(int)
    period=orm.Required(str)
    applicants=orm.Required(int)
    description=orm.Required(str)

    def Calculate(self):
        self.minusd,self.maxusd=convertCurrency(self.currency,self.minsalary,self.maxsalary)

    def __iter__(self):
        yield 'keyword',     self.keyword
        yield 'country',     self.country
        yield 'service',     self.service
        yield 'link',        self.link
        yield 'title',       self.title
        yield 'dt',          self.dt
        yield 'website',     self.website
        yield 'company',     self.company
        yield 'location',    self.location
        yield 'time',        self.time
        yield 'jobtype',     self.jobtype
        yield 'currency',    self.currency
        yield 'minsalary',   self.minsalary
        yield 'maxsalary',   self.maxsalary
        yield 'minusdsalary',self.minusdsalary
        yield 'maxusdsalary',self.maxusdsalary
        yield 'startrange',  self.startrange
        yield 'toprange',    self.toprange
        yield 'period',      self.period
        yield 'applicants',  self.applicants
        yield 'description', self.description

class Airport(db.Entity):
    _table_ = 'Airports'
    country = orm.Required(str)
    iso3 = orm.Required(str)
    city=orm.Required(str)
    code=orm.Required(str)
    short=orm.Required(bool)
    directions = orm.Set('Direction', reverse='destination')
    departures = orm.Set('Direction', reverse='departure')

class Direction(db.Entity):
    _table_ = 'Directions'
    departure=orm.Required(Airport, reverse='departures')
    destination = orm.Required(Airport, reverse='directions')
    cost = orm.Required(int)
    duration=orm.Required(int)
    distance=orm.Required(int)
    dt = orm.Required(datetime)