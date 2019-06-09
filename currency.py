import re
import requests
from four_fn import parse_arithmetic
import settings


def btc():
    r = requests.get('https://shauna.website/currency.json')
    rates = r.json()
    return rates['BTC']

def calc(s):
    s = s.casefold()
    s = re.sub('\s', '', s)
    s = re.sub('(\d+)([a-zA-Z]+)', '\\1*\\2', s)
    s = re.sub('(\([\*\+\-\/\d\(\)]*\))([a-zA-Z]+)', '\\1*\\2', s)
    try:
        return parse_arithmetic(s)    
    except:
        conv = s.split('->')
        r = requests.get('https://shauna.website/currency.json')
        rates = r.json()
        rates['BS'] = rates['VES']
        result_symbol = conv[1].rstrip().lstrip().casefold()
        expression = conv[0]
        if result_symbol.upper() in rates:
            for symbol in rates:
                symbol = symbol.casefold()
                if symbol in expression:
                    expression = expression.replace(symbol, str(1/rates[symbol.upper()]))
            amount = parse_arithmetic(expression.lstrip().rstrip())
            return '{} {}'.format(amount*rates[result_symbol.upper()], result_symbol.upper())
    return 'mongolicx'

if __name__ == '__main__':
    print(calc('2*usd-> ARS'))
    print(calc('(8*5*4*12)usd -> VES', 300))
