from pony import orm
from datetime import datetime, date
from port.mod_jobs.utils import convertCurrency

db1 = orm.Database()

class Resource(db1.Entity):
    _table_ = 'Resources'
    currency = orm.Required('Currency')
    algorythm = orm.Required(str)
    gpu = orm.Required(str)
    rew24= orm.Required(float)
    rewbtc24= orm.Required(float)
    rewusd24= orm.Required(float)
    energy=orm.Required(float)
    dt = orm.Required(date)

class ExchangeRate(db1.Entity):
    _table_ = 'ExchangeRates'
    currency = orm.Required('Currency')
    exrbtc = orm.Required(float)
    exrusd = orm.Required(float)
    dt = orm.Required(date)

class Currency(db1.Entity):
    _table_ = 'Currencies'
    resource = orm.Set(Resource, reverse='currency')
    exrates = orm.Set(ExchangeRate, reverse='currency')
    name = orm.Required(str)
    sname = orm.Required(str)
    isnh= orm.Required(bool)


class GPU(db1.Entity):
    _table_ = 'GPUs'
    name = orm.Required(str)
    link = orm.Required(str)

class GPUCost(db1.Entity):
    _table_ = 'GPUCosts'
    name = orm.Required(str)
    link = orm.Required(str)
    memory = orm.Required(int)
    cost = orm.Required(float)


