import discord
from tacobot import eightch
import settings
import asyncio
import logging
import requests
from discord.ext import commands
import random


logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix='!')

CHECK_THREAD_TIME = 300

@bot.command()
async def echo(ctx, *args):
    await ctx.send(str(' '.join(args)))

@bot.command()
async def dolar(ctx, arg):
    if arg == 'btc':
        btc_price_url = 'https://coinbase.com/api/v1/prices/spot_rate'
        localbtc_ticker_url ='https://localbitcoins.com/bitcoinaverage/ticker-all-currencies/'

        try:
            btc_price_r = requests.get(btc_price_url)
            localbtc_ticker_r  = requests.get(localbtc_ticker_url)
        except:
            message = 'no disponible'
        else:
            usdbtc = btc_price_r.json()['amount']
            
            ts = ['avg_1h', 'avg_6h', 'avg_12h', 'avg_24h']
            ts = {'avg_1h': 'promedio una hora',
                  'avg_6h': 'promedio seis horas',
                  'avg_12h': 'promedio doce horas',
                  'avg_24h': 'promedio veinticuatro horas',}
            l = []
            for t in ts:
                try:
                    l.append(' {}: {} bs/$'.format(ts[t], '%.2f' % (float(localbtc_ticker_r.json()['VES'][t])/float(usdbtc),)))
                except Exception:
                    pass
            message = 'localbitcoins:\n{}'.format('\n'.join(l))

    elif arg == 'today':
        try:
            dt = requests.get('https://s3.amazonaws.com/dolartoday/data.json').json()['USD']['dolartoday']
        except:
            message = 'no disponible'
        else:
            message = 'dolartoday: {} bs/$'.format(dt)

    await ctx.send('```{}```'.format(message))

async def new_eightch_threads():
    await bot.wait_until_ready()
    channel = bot.get_channel(settings.channel_id)
    while not bot.is_closed():
        old_catalog = eightch.read_old_catalog(settings.board)
        try:
            catalog = eightch.get_and_save_catalog(settings.board)
        except Exception as e:
            logging.error(e)
            catalog = None
        if catalog and old_catalog:
            new_threads = eightch.find_new_threads(catalog, old_catalog)
            if new_threads:
                for thread in new_threads:
                    message = 'hilo nuevo: https://8ch.net/{}/res/{}.html'.format(settings.board, thread)
                    await channel.send(message)
            else:
                logging.info('no new threads')
        await asyncio.sleep(CHECK_THREAD_TIME)

@bot.event
async def on_ready():
    bot.loop.create_task(new_eightch_threads())

@bot.event
async def on_message(message):
    if message.content.casefold().startswith('colomb'):
        await message.channel.send('malditos colombianos')
    await bot.process_commands(message)


bot.run(settings.token)
