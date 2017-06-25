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
    with orm.db_session:
        algorythms=orm.select((s.algorythm, orm.avg(s.rewusd24), orm.count(s.rewusd24)) for s in Resource if s.gpu==gpu).order_by(1)[:]
        algorythmsn=orm.select((s.algorythm, orm.count(s.currency)) for s in Resource if s.gpu==gpu).order_by(1)[:]
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
    dataseries=[Bar(x=xr,y=yr, marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1)))]
    graphavg = getplotly(dataseries,Layout(title='%s Average Profitability, $'%gpu))
    xr=[x[0] for x in algorythms]
    yr=[x[1] for x in algorythms]
    wr=[x[1] for x in algorythmsn]
    dataseries=[Bar(x=xr,y=yr,name='Avg Profit', marker = dict(color = colors0[4], line=dict(color=colors1[4],width=1))),
                Bar(x=xr,y=wr,name='# of Currencies', marker = dict(color = colors0[5], line=dict(color=colors1[5],width=1)))]
    graphalg = getplotly(dataseries,Layout(title='Algorythms on %s, $'%gpu))
    menu=menu=getmenu()
    return render_template('ccm/gpu.jade',menu=menu,title=gpu,graph=graph,graphavg=graphavg,graphalg=graphalg)

@mod_ccm.route('/currency/<cid>', methods=['GET'], endpoint='show_currency')
def show_currency(cid):
    graph = ''
    dataseries=[]
    avgprof=[]
    maxprof=[]
    with orm.db_session:
        currency=Currency.get(sname=cid)
        cer=orm.select((s.dt,s.exrusd) for s in ExchangeRate if s.currency==currency).order_by(1)[:]
        btcer=orm.select((s.dt,s.exrusd) for s in ExchangeRate if s.currency.id==1).order_by(1)[:]
        gpuavg=orm.select((s.gpu, orm.avg(s.rewusd24)) for s in Resource if s.currency==currency).order_by(1)[:]
        xr=orm.select((c.dt) for c in Resource if c.currency==currency)[:]
        c=0
        for gpu in gpuavg:
            yr=orm.select((c.rewusd24) for c in Resource if c.gpu==gpu[0] and c.currency==currency)[:]
            dataseries.append(Scatter(x=xr,y=yr,name=gpu[0], marker = dict(color = colors0[c])))
            c+=1
    title='%s Daily Profitability, $'%currency.name
    graph = getplotly(dataseries,Layout(title=title))
    xr=[x[0] for x in gpuavg]
    yr=[x[1] for x in gpuavg]
    dataseries=[Bar(x=xr,y=yr, marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1)))]
    graphavg = getplotly(dataseries,Layout(title='%s Average Profitability, $'%currency.name))
    yr1=[x[1] for x in cer]
    xr=[x[0] for x in cer]
    yr2=[x[1] for x in btcer]
    dataseries=[Scatter(x=xr,y=yr1,name=currency.sname, marker = dict(color = colors0[0], line=dict(color=colors1[0],width=1))),
                Scatter(x=xr,y=yr2,name='BTC',yaxis='y2', marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1)))]
    grapher = getplotly(dataseries,Layout(title='%s and BTC Exchange Rates, $'%currency.sname,yaxis=dict(title='%s Exchange Rate, $'%currency.sname),yaxis2=dict(title='BTC Exchange Rate, $',overlaying='y',side='right')))
    menu=menu=getmenu()
    return render_template('ccm/exrates.jade',menu=menu,title=currency.name,graph=graph,graphavg=graphavg,grapher=grapher)

@mod_ccm.route('/algorythm/<algorythm>', methods=['GET'], endpoint='show_algorythm')
def show_algorythm(algorythm):
    graph = ''
    dataseries=[]
    avgprof=[]
    maxprof=[]
    with orm.db_session:
        gpuavg=orm.select((s.gpu, orm.avg(s.rewusd24)) for s in Resource if s.algorythm==algorythm).order_by(orm.desc(1))
        xr=orm.select((c.dt) for c in Resource if c.currency==currency)[:]
        currencies=orm.select((c.name) for c in Resource if c.algorythm==algorythm)[:]
        c=0
        for curr in currencies:
            yr=orm.select((c.rewusd24) for c in Resource if c.gpu==gpu[0] and c.currency==curr)[:]
            dataseries.append(Scatter(x=xr,y=yr,name=gpu[0], marker = dict(color = colors0[c])))
            c+=1
    title='%s Daily Profitability, $'%currency.name
    graph = getplotly(dataseries,Layout(title=title))
    xr=[x[0] for x in gpuavg]
    yr=[x[1] for x in gpuavg]
    dataseries=[Bar(x=xr,y=yr, marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1)))]
    graphavg = getplotly(dataseries,Layout(title='GPUs Average Profitability on %s, $'%algorythm))
    menu=menu=getmenu()
    return render_template('ccm/gpu.jade',menu=menu,title=gpu,graph=graph,graphavg=graphavg)

@mod_ccm.route('/', methods=['GET'], endpoint='show')
def show():
    crawler=WTMCrawler()
    crawler.Start()
    graph = ''
    dataseries=[]
    prof1=[]
    prof2=[]
    prof3=[]
    roi1=[]
    roi2=[]
    roi3=[]
    weekly1=[]
    weekly2=[]
    weekly3=[]
    with orm.db_session:
        gpucost=orm.select((c.name,c.cost) for c in GPUCost).order_by(1)[:]
        yr=[x[1] for x in gpucost]
        gpus=[x[0] for x in gpucost]
        for x in gpucost:
            curravg=orm.select((s.currency, orm.avg(s.rewusd24)) for s in Resource if s.gpu==x[0]).order_by(orm.desc(2))[:]
            avg1=orm.avg(p.rewusd24 for p in Resource if p.gpu==x[0] and p.currency==curravg[0][0])
            avg2=orm.avg(p.rewusd24 for p in Resource if p.gpu==x[0] and p.currency==curravg[1][0])
            avg3=orm.avg(p.rewusd24 for p in Resource if p.gpu==x[0] and p.currency==curravg[2][0])
            prof1.append(avg1*100)
            prof2.append(avg2*100)
            prof3.append(avg3*100)
            roi1.append(avg1/x[1]*100)
            roi2.append(avg2/x[1]*100)
            roi3.append(avg3/x[1]*100)
            weekly1.append(avg1*7)
            weekly2.append(avg2*7)
            weekly3.append(avg3*7)
        dataseries.append(Bar(x=gpus,y=yr,name='GPU Cost', marker = dict(color = colors0[0], line=dict(color=colors1[0],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=prof1,name='Top Currency', marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=prof2,name='2nd Currency', marker = dict(color = colors0[4], line=dict(color=colors1[4],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=prof3,name='3rd Currency', marker = dict(color = colors0[5], line=dict(color=colors1[5],width=1.5,))))
        graph = getplotly(dataseries,Layout(title='GPU Cost and 100-Days Profitability, $', xaxis=dict(type='category' )))
        dataseries=[]
        dataseries.append(Bar(x=gpus,y=roi1,name='Top Currency', marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=roi2,name='2nd Currency', marker = dict(color = colors0[4], line=dict(color=colors1[4],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=roi3,name='3rd Currency', marker = dict(color = colors0[5], line=dict(color=colors1[5],width=1.5,))))
        graphroi = getplotly(dataseries,Layout(title='GPU Daily ROI, %', xaxis=dict(type='category' )))
        dataseries=[]
        dataseries.append(Bar(x=gpus,y=weekly1,name='Top Currency', marker = dict(color = colors0[3], line=dict(color=colors1[3],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=weekly2,name='2nd Currency', marker = dict(color = colors0[4], line=dict(color=colors1[4],width=1.5,))))
        dataseries.append(Bar(x=gpus,y=weekly3,name='3rd Currency', marker = dict(color = colors0[5], line=dict(color=colors1[5],width=1.5,))))
        graphweekly = getplotly(dataseries,Layout(title='Weekly Profit, $', xaxis=dict(type='category' )))
    menu=getmenu()
    return render_template('ccm/ccm.jade',menu=menu,graph=graph,graphroi=graphroi,graphweekly=graphweekly)

def getmenu():
    currencies=[]
    lastdate=date.today()
    with orm.db_session:
        lastdate=orm.max(p.dt for p in Resource)
        firstdate=orm.min(p.dt for p in Resource)
        currencies=Currency.select(lambda p: p.id>1).order_by(Currency.name)[:]
        gpus=orm.select((c.name) for c in GPUCost).order_by(1)[:]
    return render_template('ccm/menu.jade',currencies=currencies,gpus=gpus)


def getplotly(dataseries,layout):
    config={}
    config['showLink'] = False
    figure_or_data = { "data": dataseries, "layout":layout }
    plot_html = plot_html, plotdivid, width, height = _plot_html(figure_or_data,config, False, 1000, 600, False)
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
