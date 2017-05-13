import re

def convertCurrency(currency, minsalary, maxsalary):
    if maxsalary=='':
        maxsalary='0'
    if currency=='&pound;':
        er=1.28
    elif currency=='&euro;':
        er=1.09
    elif currency=='AU$':
        er=0.75
    elif currency=='NZ$':
        er=0.69
    else:
        er=1
    return [int(float(minsalary)*er), int(float(maxsalary)*er)]

