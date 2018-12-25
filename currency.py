import re
import requests
from four_fn import parse_arithmetic
import settings

OER_API_URL = 'https://openexchangerates.org/api/latest.json?app_id={}'.format(settings.fixer_id)

def btc():
    r = requests.get(OER_API_URL)
    rates = r.json()['rates']
    return rates['BTC']

def calc(s, bs=None):
    s = s.casefold()
    s = re.sub('\s', '', s)
    s = re.sub('(\d+)([a-zA-Z]+)', '\\1*\\2', s)
    s = re.sub('(\([\*\+\-\/\d\(\)]*\))([a-zA-Z]+)', '\\1*\\2', s)
    try:
        return parse_arithmetic(s)    
    except:
        assert ('ves' not in s.casefold() and 'bs' not in s.casefold()) or bs != None
        conv = s.split('->')
        r = requests.get(OER_API_URL)
        rates = r.json()['rates']
        result_symbol = conv[1].rstrip().lstrip().casefold()
        expression = conv[0]
        rates['VES'] = bs
        rates['BS'] = bs
        if result_symbol.upper() in rates:
            for symbol in rates:
                symbol = symbol.casefold()
                if symbol in expression:
                    expression = expression.replace(symbol, str(1/rates[symbol.upper()]))
            amount = parse_arithmetic(expression.lstrip().rstrip())
            return '{} {}'.format(amount*rates[result_symbol.upper()], result_symbol.upper())
    return 'mongolico'

if __name__ == '__main__':
    print(calc('2*usd-> ARS'))
    print(calc('(8*5*4*12)usd -> VES', 300))
