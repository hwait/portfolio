from flask import Blueprint, render_template, url_for,request, redirect
from port.mod_jobs.business.GBCrawler import GBCrawler
from port.mod_jobs.business.AUSCrawler import AUSCrawler
from port.mod_jobs.business.NZCrawler import NZCrawler
from pony import orm
from port.mod_jobs.models import *
from port.mod_jobs.forms import SearchForm,ListForm,AnalyticForm,AirportsForm
import flask_excel as excel
from datetime import date,timedelta,datetime
import plotly 
from plotly.offline.offline import _plot_html
from plotly.graph_objs import Box, Layout, Bar
import csv
from rapidconnect import RapidConnect
from forex_python.converter import CurrencyRates,RatesNotAvailableError

#from flask_weasyprint import HTML, render_pdf

mod_jobs=Blueprint('jobs', __name__, url_prefix='/jobs')

allcountries={'AUS': 'Australia', 'CAN': 'Canada', 'GB': 'Great Britain', 'NZ': 'New Zealand', 'POR': 'Portugal', 'USCAL': 'USA / Caligornia', 'USMIA': 'USA / Miami'}
colors0=['rgb(240,98,146)', 'rgb(186,104,200)','rgb(121,134,203)','rgb(79,195,247)', 'rgb(77,182,172)', 'rgb(129,199,132)','rgb(220,231,117)','rgb(255,213,79)', 'rgb(255,138,101)','rgb(161,136,127)']
colors1=['rgb(216,27,96)',  'rgb(142,36,170)', 'rgb(57,73,171)',  'rgb(3,155,229)',  'rgb(0,137,123)',  'rgb(67,160,71)',  'rgb(192,202,51)', 'rgb(253,216,53)', 'rgb(244,81,30)',  'rgb(109,76,65)']

@mod_jobs.route('/maps/', methods=['GET','POST'], endpoint='maps')
def maps():
    form = AirportsForm(request.form)
    departure=None
    rate=1
    mapcost=''
    mapduration=''
    mapeasiness=''
    msg=''
    did=''
    with orm.db_session:
        logs=Log.select(lambda p: p.country=='AIR').order_by(orm.desc(Log.id))[:]
        previous=orm.select(c.departure for c in Direction).prefetch(Airport)[:]
        
        if logs[0].dt+timedelta(days=1)>datetime.now():
            delta=(logs[0].dt+timedelta(days=1)-datetime.now()).seconds
            hours=(delta//3600)
            minutes=(delta-hours*3600)//60
            msg='New search will be available in %s hour(s) %s minutes.'%(hours,minutes)
        else:
            airports=Airport.select().order_by(Airport.country)[:]
            form.airports.choices = [(x.id, '%s - %s, %s'%(x.country,x.code, x.city)) for x in airports]
    if request.method == 'GET':
        did=request.values.get('did','')
        currency='USD'
        if did!='':
            cr = CurrencyRates()
            with orm.db_session:
                departure=Airport.get(id=int(did))
                #directions=Direction.select(lambda p: p.departure==departure).prefetch(Airport)[:]
                directions=Direction.select_by_sql('select d0.* from Directions d0 join Airports a0 on a0.id=d0.destination where d0.cost=(select min(d.cost) from Directions d join Airports a on a.id=d.destination where a.country=a0.country and d.departure=d0.departure) and departure=%s'%departure.id)
                try:
                    rate=cr.get_rate(directions[0].currency, 'USD')
                except RatesNotAvailableError:
                    if directions[0].currency=='KZT':
                        rate=0.0032
                    else:
                        rate=1
                        currency=directions[0].currency
                locations=[d.destination.iso3 for d in directions]
                texts=['%s - %s, %s'%(d.destination.country,d.destination.code,d.destination.city) for d in directions]
                vals=[int(d.cost*rate) for d in directions]
                costperm=[int(d.cost*rate*d.duration/float(d.distance)) for d in directions]
                times=[d.duration//60 for d in directions]
                mapcost=makemap('Flight cost from %s to some countries.'%departure.code,'Cost, %s'%currency,locations,vals,texts)
                mapduration=makemap('Total flight duration, best from 3 most cheap flight.','Duration, hours',locations,times,texts)
                mapeasiness=makemap('Easiness (cost * duration / distance).','Easiness, $*h/mi',locations,costperm,texts)
    elif form.validate_on_submit() and msg=='':
        with orm.db_session:
            dtstr=(datetime.now()+timedelta(days=30)).strftime('%Y-%m-%d')
            departure=Airport.get(id=int(request.form.get('airports')))
            iteration=orm.max(p.iteration for p in Direction if p.departure==departure)
            if iteration==None:
                iteration=0
            if iteration<3:
                iteration+=1
            else:
                iteration=1
            dirs=Direction.select(lambda p: p.departure==departure and p.iteration==iteration).delete(bulk=True)
            portstodo=Airport.select(lambda p: p.iteration==iteration and p.code!=departure.code)[:]
            rapid = RapidConnect("flight-167611", "12489be9-a1b2-442f-9f98-77609a7d6a9d")
            for x in portstodo:
                processdestination(rapid,departure,x,dtstr, iteration)
            log = Log(keyword='none', dt=datetime.now(),country='AIR')
            return redirect('%s?did=%s'%(url_for('maps'),departure.id))
    return render_template('parsers/maps.jade',form=form,msg=msg,departure=departure,previous=previous,mapcost=mapcost,mapduration=mapduration,mapeasiness=mapeasiness)

def makemap(title,bartitle,locations,z,text):
    data = [ dict(
        type = 'choropleth',
        locations = locations,
        z = z,
        text = text,
        colorscale = [[0,"rgb(198, 40, 40)"],[0.35,"rgb(239, 108, 0)"],[0.5,"rgb(249, 168, 37)"],\
            [0.6,"rgb(158, 157, 36)"],[0.7,"rgb(85, 139, 47)"],[1,"rgb(27, 94, 32)"]],
        autocolorscale = False,
        reversescale = True,
        marker = dict(
            line = dict (
                color = 'rgb(180,180,180)',
                width = 0.5
            ) ),
        colorbar = dict(
            autotick = False,
            tickprefix = '',
            title = bartitle),
      ) ]
    layout = dict(title = title,  geo = dict(showframe = False,showcoastlines = True, projection = dict(type = 'Mercator')))
    return getplotly(data, layout)

def processdestination(rapid,departure,destination, dt,iteration):
    result = rapid.call('GoogleFlightsAPI', 'searchSingleTrip', { 
        'apiKey': 'AIzaSyCpwveOqrybDi5itOEQax84QWGgxmKaVoM',
        'origin': departure.code, 
        'destination': destination.code,
        'passengersAdultCount': '1','passengersChildCount': '0','fromDate': dt,	'toDate': '','maxPrice': '','refundable': '','solutions': '3'})
    if not 'tripOption' in result['trips']:
        return
    solutions=result['trips']['tripOption']
    saletotal=solutions[0]['saleTotal']
    cost=int(saletotal[3:].split('.')[0])
    currency=saletotal[:3]
    duration=min(int(x['slice'][0]['duration']) for x in solutions)
    distance=0
    for x in solutions[0]['slice'][0]['segment']:
        distance+=int(x['leg'][0]['mileage'])
    obj=Direction(departure=departure,destination=destination,dt=dt,cost=cost,duration=duration,distance=distance,currency=currency,iteration=iteration)
    orm.commit()

@mod_jobs.route('/search/graph/', methods=['GET'], endpoint='graph')
def jobsanalysis():
    with orm.db_session:
        countriesset=set(orm.select((c.country) for c in Stat)[:])
        keywords=orm.select((c.keyword) for c in Stat)[:]
    countries= [ (k, allcountries[k]) for k in countriesset ]
    #form.country.choices = countries
    #form.keyword.choices = [(x, x) for x in keywords]
    if request.method == 'GET':
        dataseries=[]
        popularity=[]
        plotly.tools.set_credentials_file(username='hwait', api_key='mYs3EJORl98E0vxkWvGr')
        keyword=''
        countrytext=''
        c=0
        country=request.values.get('c','')
        if country in allcountries:
            countrytext=allcountries[country]
            with orm.db_session:
                localarr=orm.select((c.keyword) for c in JobEntity if c.country==country)[:]
                for key in localarr:
                    yr=orm.select((c.minusdsalary) for c in JobEntity if c.country==country and c.period=='annum' and c.keyword==key)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Start %s'%key, marker = dict(color = colors0[c])))
                    yr=orm.select((c.maxusdsalary) for c in JobEntity if c.country==country and c.period=='annum' and c.keyword==key)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Top %s'%key, marker = dict(color = colors1[c])))
                    title='Salaries in %s for known keywords.'%countrytext
                    vacancies,days=orm.select((c.total,c.days) for c in Stat if c.country==country and c.period=='annum' and c.keyword==key)[:][0]
                    popularity.append(int(int(vacancies)/int(days)))
                    c+=1
        else:
            keyword=request.values.get('k','')
            with orm.db_session:
                localarr=orm.select((c.country) for c in JobEntity if c.keyword==keyword)[:]
                for cnt in localarr:
                    yr=orm.select((c.minusdsalary) for c in JobEntity if c.keyword==keyword and c.period=='annum' and c.country==cnt)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Start %s'%cnt, marker = dict(color = colors0[c])))
                    yr=orm.select((c.maxusdsalary) for c in JobEntity if c.keyword==keyword and c.period=='annum' and c.country==cnt)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Top %s'%cnt, marker = dict(color = colors1[c])))
                    title='Salaries for jobs with keyword "%s".'%keyword
                    vacancies,days=orm.select((c.total,c.days) for c in Stat if c.country==cnt and c.period=='annum' and c.keyword==keyword)[:][0]
                    popularity.append(int(int(vacancies)/int(days)))
                    c+=1
        graph = getplotly(dataseries,Layout(title=title))
        dataseries_pop=[Bar(x=localarr,y=popularity)]
        graphp = getplotly(dataseries_pop,Layout(title='Relevance, vacancies per day'))
    return render_template('parsers/graph.jade',countries=countries,keywords=keywords,country=countrytext,keyword=keyword,graph=graph,graphp=graphp)

def getplotly(dataseries,layout):
    config={}
    config['showLink'] = False
    figure_or_data = { "data": dataseries, "layout":layout }
    plot_html = plot_html, plotdivid, width, height = _plot_html(figure_or_data,config, False, '100%', 600, False)
    resize_script = ''
    if width == '100%' or height == '100%':
        resize_script = (
            ''
            '<script type="text/javascript">'
            'window.removeEventListener("resize");'
            'window.addEventListener("resize", function(){{'
            'Plotly.Plots.resize(document.getElementById("{id}"));}});'
            '</script>'
        ).format(id=plotdivid)
    graph = ''.join([plot_html, resize_script])
    return graph

@mod_jobs.route('/search/list/', methods=['POST'], endpoint='list')
def jobslist():
    data=[]
    country=''
    form = ListForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        ids=form.ids.data.split(',')
        for x in ids:
            with orm.db_session:
                job=JobEntity.get(id=x)
                data.append(dict(job))
                if country=='':
                    country=data[0]['country']
        if form.returntype.data=='0':
            return excel.make_response_from_records(data, 'csv', file_name='jobs_%s.csv'%country)
        elif form.returntype.data=='1':
            return excel.make_response_from_records(data, 'xlsx', file_name='jobs_%s.xlsx'%country)
        elif form.returntype.data=='2':
            getDescriptions(data, country)
            return render_template('parsers/selectedjobs.jade', data=data)
            #html = render_template('parsers/parsers.jade', data=data, form=ListForm(), keyword='', country=country)
            #return render_pdf(HTML(string=html))
    return ('', 204)

@mod_jobs.route('/search/', methods=['GET','POST'])
def jobsearch():
    form = SearchForm(request.form)
    with orm.db_session:
        prevmaps=orm.select(c.departure for c in Direction).prefetch(Airport)[:]
        logs=Log.select(lambda p: p.country!='AIR').order_by(orm.desc(Log.id))[:]
    if request.method == 'GET':
        keyword = request.args.get('k', '')
        country = request.args.get('c', '')
        if keyword=='':
            return renderform(form,logs,prevmaps)
        else:
            return renderjobs(kw=keyword,country=country)
    else:
        if form.validate_on_submit():
            keyword=form.keyword.data
            country=form.country.data
            #if keyword==logs[0].keyword and logs[0].dt+timedelta(hours=1)>datetime.now():
            if keyword==logs[0].keyword and logs[0].dt+timedelta(seconds=1)>datetime.now():
                return renderjobs(kw=keyword,country=country)
            else:
                return renderjobs(kw=keyword,country=country,isrefresh=True)
        else:
            return renderform(form,logs,prevmaps)

def renderform(form, logs=[], prevmaps=[]):
    message=''
    prevkw=''
    if len(logs)>0:
        prevkw=logs[0].keyword
        prevdt=logs[0].dt
        prevcountry=logs[0].country
        #if prevdt+timedelta(hours=1)>datetime.now():
        if prevdt+timedelta(seconds=1)>datetime.now():
            message='Previous search "%s" for %s was completed less then an hour. New search will be available in %s minutes' % (prevkw,allcountries[prevcountry],((prevdt+timedelta(hours=1)-datetime.now()).seconds//60)%60)
    return render_template('parsers/searchform.jade', msg=message, form=form,prevkey=prevkw,logs=logs,countries=allcountries,prevmaps=prevmaps)

def renderjobs( kw='', country='', isrefresh=False):
    form = ListForm()
    if isrefresh:
        if country=='GB':
            jc=GBCrawler(keyword=kw)
            jc.Start()
        elif country=='AUS':
            jc=AUSCrawler(keyword=kw)
            jc.Start()
        elif country=='NZ':
            jc=NZCrawler(keyword=kw)
            jc.Start()
    with orm.db_session:
        items=JobEntity.select(lambda p: p.keyword==kw and p.country==country)[:]
        #for x in items:
        #    x.Calculate()
    return render_template('parsers/alljobs.jade', data=items, form=form, keyword=kw, country=allcountries[country])

def getDescriptions(data, country):
    if country=='GB':
        jc=GBCrawler()
        for x in data:
            if x['service']=='www.cwjobs.co.uk':
                x['description']=jc.ParseCwjobsPage(x['link'])
            elif x['service']=='reed.co.uk':
                x['description']=jc.ParseReedPage(x['link'])
    elif country=='AUS':
        jc=AUSCrawler()
        for x in data:
            if x['service']=='www.seek.com.au':
                x['description']=jc.ParseSeekPage(x['link'])
            elif '/details/' in x['link']:
                x['description']=jc.ParseAdzunaPage(x['link'])
    elif country=='NZ':
        jc=NZCrawler()
        for x in data:
            x['description']=jc.ParseSeekPage(x['link'])