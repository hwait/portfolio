from flask import Blueprint, render_template, url_for,request
from port.mod_parser.business.GBCrawler import GBCrawler
from port.mod_parser.business.AUSCrawler import AUSCrawler
from port.mod_parser.business.NZCrawler import NZCrawler
from pony import orm
from port.mod_parser.models import *
from port.mod_parser.forms import SearchForm,ListForm,AnalyticForm
import flask_excel as excel
from datetime import date,timedelta,datetime
import plotly 
from plotly.offline.offline import _plot_html
from plotly.graph_objs import Box, Layout


#from flask_weasyprint import HTML, render_pdf



mod_parser=Blueprint('parsers', __name__, url_prefix='/jobs')
allcountries={'AUS': 'Australia', 'CAN': 'Canada', 'GB': 'Great Britain', 'NZ': 'New Zealand', 'POR': 'Portugal', 'USCAL': 'USA / Caligornia', 'USMIA': 'USA / Miami'}
colors0=['rgb(240,98,146)', 'rgb(186,104,200)','rgb(121,134,203)','rgb(79,195,247)', 'rgb(77,182,172)', 'rgb(129,199,132)','rgb(220,231,117)','rgb(255,213,79)', 'rgb(255,138,101)','rgb(161,136,127)']
colors1=['rgb(216,27,96)',  'rgb(142,36,170)', 'rgb(57,73,171)',  'rgb(3,155,229)',  'rgb(0,137,123)',  'rgb(67,160,71)',  'rgb(192,202,51)', 'rgb(253,216,53)', 'rgb(244,81,30)',  'rgb(109,76,65)']
@mod_parser.route('/search/graph/', methods=['GET'], endpoint='graph')
def jobsanalysis():
    with orm.db_session:
        countriesset=set(orm.select((c.country) for c in Stat)[:])
        keywords=orm.select((c.keyword) for c in Stat)[:]
    countries= [ (k, allcountries[k]) for k in countriesset ]
    #form.country.choices = countries
    #form.keyword.choices = [(x, x) for x in keywords]
    if request.method == 'GET':
        dataseries=[]
        plotly.tools.set_credentials_file(username='hwait', api_key='mYs3EJORl98E0vxkWvGr')
        keyword=''
        countrytext=''
        c=0
        country=request.values.get('c','')
        if country in allcountries:
            countrytext=allcountries[country]
            with orm.db_session:
                localkeywords=orm.select((c.keyword) for c in JobEntity if c.country==country)[:]
                for key in localkeywords:
                    yr=orm.select((c.minusdsalary) for c in JobEntity if c.country==country and c.period=='annum' and c.keyword==key)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Start %s'%key, marker = dict(color = colors0[c])))
                    yr=orm.select((c.maxusdsalary) for c in JobEntity if c.country==country and c.period=='annum' and c.keyword==key)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Top %s'%key, marker = dict(color = colors1[c])))
                    title='Starting salaries in %s.'%countrytext
                    c+=1
        else:
            keyword=request.values.get('k','')
            with orm.db_session:
                localcountries=orm.select((c.country) for c in JobEntity if c.keyword==keyword)[:]
                for cnt in localcountries:
                    yr=orm.select((c.minusdsalary) for c in JobEntity if c.keyword==keyword and c.period=='annum' and c.country==cnt)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Start %s'%cnt, marker = dict(color = colors0[c])))
                    yr=orm.select((c.maxusdsalary) for c in JobEntity if c.keyword==keyword and c.period=='annum' and c.country==cnt)[:]
                    dataseries.append(Box(y=yr,boxpoints = False,name = 'Top %s'%cnt, marker = dict(color = colors1[c])))
                    title='Starting salaries for jobs with "%s".'%keyword
                    c+=1
        config={}
        config['showLink'] = False
        figure_or_data = { "data": dataseries, "layout":Layout(title=title) }
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
    return render_template('parsers/graph.jade',countries=countries,keywords=keywords,country=countrytext,keyword=keyword,graph=graph)

@mod_parser.route('/search/list/', methods=['POST'], endpoint='list')
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

@mod_parser.route('/search/', methods=['GET','POST'])
def jobsearch():
    form = SearchForm(request.form)
    with orm.db_session:
        logs=Log.select().order_by(orm.desc(Log.id))[:]
    if request.method == 'GET':
        keyword = request.args.get('k', '')
        country = request.args.get('c', '')
        if keyword=='':
            return renderform(form,logs)
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
            return renderform(form,logs)

def renderform(form, logs=[]):
    message=''
    prevkw=''
    if len(logs)>0:
        prevkw=logs[0].keyword
        prevdt=logs[0].dt
        prevcountry=logs[0].country
        #if prevdt+timedelta(hours=1)>datetime.now():
        if prevdt+timedelta(seconds=1)>datetime.now():
            message='Previous search "%s" for %s was completed less then an hour. New search will be available in %s minutes' % (prevkw,allcountries[prevcountry],((prevdt+timedelta(hours=1)-datetime.now()).seconds//60)%60)
    return render_template('parsers/searchform.jade', msg=message, form=form,prevkey=prevkw,logs=logs,countries=allcountries)

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