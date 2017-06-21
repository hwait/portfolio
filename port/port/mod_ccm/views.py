from flask import Blueprint, render_template, url_for,request, redirect
from port.mod_ccm.logic import WTMCrawler
from port.mod_ccm.models import *
from datetime import date,timedelta,datetime
import plotly 
from plotly.offline.offline import _plot_html
from plotly.graph_objs import Box, Layout, Bar,Scatter
import csv

mod_ccm=Blueprint('ccm', __name__, url_prefix='/ccm')

colors0=['rgb(240,98,146)', 'rgb(186,104,200)','rgb(121,134,203)','rgb(79,195,247)', 'rgb(77,182,172)', 'rgb(129,199,132)','rgb(220,231,117)','rgb(255,213,79)', 'rgb(255,138,101)','rgb(161,136,127)']
colors1=['rgb(216,27,96)',  'rgb(142,36,170)', 'rgb(57,73,171)',  'rgb(3,155,229)',  'rgb(0,137,123)',  'rgb(67,160,71)',  'rgb(192,202,51)', 'rgb(253,216,53)', 'rgb(244,81,30)',  'rgb(109,76,65)']

@mod_ccm.route('/gpu/<gpu>', methods=['GET'], endpoint='show_gpu')
def show_gpu(gpu):
    graph = ''
    dataseries=[]
    avgprof=[]
    maxprof=[]
    currencies,gpus,lastdate=getcurrencies()
    with orm.db_session:
        curs=orm.select((s.currency, orm.avg(s.rewusd24)) for s in Resource if s.gpu==gpu).order_by(orm.desc(2))[:10]
        xr=orm.select((c.dt) for c in Resource if c.gpu==gpu)[:]
        c=0
        for currency in curs:
            yr=orm.select((c.rewusd24) for c in Resource if c.gpu==gpu and c.currency==currency[0])[:]
            dataseries.append(Scatter(x=xr,y=yr,name=currency[0].name, marker = dict(color = colors0[c])))
            c+=1
    title='%s Daily Profitability, $'%gpu
    graph = getplotly(dataseries,Layout(title=title))
    xr=[x[0].sname for x in curs]
    yr=[x[1] for x in curs]
    dataseries=[Bar(x=xr,y=yr, marker = dict(color = colors0[0], line=dict(color=colors1[0],width=1)))]
    graphavg = getplotly(dataseries,Layout(title='%s Average Profitability, $'%gpu))
    return render_template('ccm/gpu.jade',graph=graph,graphavg=graphavg,currencies=currencies,date=lastdate,gpus=gpus)


@mod_ccm.route('/', methods=['GET'], endpoint='show')
def show():
    graph = ''
    dataseries=[]
    avgprof=[]
    maxprof=[]
    currencies,gpus,lastdate=getcurrencies()
    with orm.db_session:
        yr=orm.select((c.cost) for c in GPUCost)[:]
        for x in gpus:
            avgprof.append(orm.avg(p.rewusd24*25 for p in Resource if p.gpu==x))
            maxprof.append(orm.max(p.rewusd24*25 for p in Resource if p.gpu==x))
        title='GPU Cost and 100-Days Profitability, $'
        dataseries.append(Bar(x=gpus,y=yr,name='GPU Cost', marker = dict(color = colors0[0], line=dict(color=colors1[0],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=maxprof,name='Max Profit', marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=avgprof,name='Avg Profit', marker = dict(color = colors0[2], line=dict(color=colors1[2],width=1.5,))))
        graph = getplotly(dataseries,Layout(title=title, xaxis=dict(type='category' )))
    if request.method == 'GET':
        crawler=WTMCrawler()
        #crawler.Start()
    return render_template('ccm/ccm.jade',graph=graph,currencies=currencies,date=lastdate,gpus=gpus)

def getcurrencies():
    currencies=[]
    lastdate=date.today()
    with orm.db_session:
        lastdate=orm.max(p.dt for p in Resource)
        firstdate=orm.min(p.dt for p in Resource)
        currencies=Currency.select(lambda p: p.id>1).order_by(Currency.name)[:]
        gpus=orm.select((c.name) for c in GPUCost)[:]
    return currencies,gpus,lastdate


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
