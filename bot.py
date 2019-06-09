import io
import re
import json
import discord
from tacobot import eightch
import settings
import asyncio
import logging
import requests
from discord.ext import commands
import random
import datetime
import shutil
import os
import sqlite3
import textwrap
import currency
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np


logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix='!')

CHECK_THREAD_TIME = 300
PRECIO_DOLAR = None
conn = sqlite3.connect(settings.prices_file)
cursor = conn.cursor()


def precio(query, sort=None):
    query = query.upper()
    sql_query = ("SELECT p.name, p.price "
                 "FROM products p "
                 "INNER JOIN ( "
                 "    SELECT name, MAX(created_at) as MaxDate "
                 "    FROM products "
                 "    GROUP BY name "
                 ") pm on p.name = pm.name and p.created_at = pm.MaxDate "
                 "WHERE p.name LIKE ? "
                 "AND p.available = 1 "
                 "AND p.created_at > date('now', '-14 days') "
                 "ORDER BY price DESC")
    cursor.execute(sql_query, ('%{}%'.format(query),))
    results = cursor.fetchall()
#    results = set((n, p) for (n, p) in results if query in n.split())
    results = set(results)
    results = list(results)
    
    if sort == 'asc':
        results = sorted(results, key=lambda x: x[1])
    elif sort == 'desc':
        results = sorted(results, key=lambda x: -x[1])
    else:
        random.shuffle(results)

    s = '`'
    if results:
        for row in results[:5]:
            if PRECIO_DOLAR:
                s += '{} a {} bolivares (~{}$)\n'.format(row[0], int(row[1]), round(row[1]/PRECIO_DOLAR, 2))
            else:
                s += '{} a {} bolivares\n'.format(row[0], int(row[1]))
    else:
        s += 'no se mano'
    s += '`'
    return s

def show_chan_sampling(back=1):
    with open(settings.chan_sample_file) as f:
        samples = json.loads(f.read())
    
    last = samples[-1]
    try:
        other = samples[-1-back]
    except:
        return 'solo tengo {} datos'.format(len(samples))
    delta = (datetime.datetime.strptime(last['timestamp'], "%Y-%m-%d %H:%M:%S.%f") -
             datetime.datetime.strptime(other['timestamp'], "%Y-%m-%d %H:%M:%S.%f"))
    posts_ve = last['count']['ve']-other['count']['ve']
    posts_arepa = last['count']['arepa']-other['count']['arepa']
    if 3600 > delta.seconds >= 60:
        mins = delta.seconds/60 
        return 'posts en los ultimos {0:.1f} mins: ve -> {1}, arepa -> {2}'.format(mins, posts_ve, posts_arepa)
    elif delta.seconds >= 3600:
        hours = delta.seconds/3600
        return 'posts en los ultimas {0:.1f} horas: ve -> {1}, arepa -> {2}'.format(hours, posts_ve, posts_arepa)
    else:
        days = delta.seconds/(3600*24)
        return 'posts en los ultimos {0:.1f} dias: ve -> {1}, arepa -> {2}'.format(days, posts_ve, posts_arepa)

def chan_plot(k=0):
    assert k == 0 or k >= 2
    def to_datetime(s):
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")

    with open('chan_sample.json') as f:
        samples = json.loads(f.read())[-k:]

    times = tuple(to_datetime(sample['timestamp']) for sample in samples)
    delta_ve = tuple(samples[k]['count']['ve']-samples[k-1]['count']['ve'] for k in range(1, len(samples)))
    delta_arepa = tuple(samples[k]['count']['arepa']-samples[k-1]['count']['arepa'] for k in range(1, len(samples)))

    plt.clf()
    plot_ve, = plt.plot(times[1:], np.cumsum(delta_ve), 'r-', label='posts /ve/')
    plot_arepa, = plt.plot(times[1:], np.cumsum(delta_arepa), 'b-', label='posts /arepa/')
    plt.legend(handles=[plot_ve, plot_arepa])

    f = io.BytesIO()
    plt.savefig(f)
    f.seek(0)
    return f

@bot.command()
async def time(ctx):
    if ctx.message.channel.name == 'otro':
        await ctx.send('`{}`'.format(datetime.datetime.now()))

@bot.command()
async def chansplot(ctx, *args):
    if ctx.message.channel.name == 'otro':
        try:
            assert len(args) <= 1
            if len(args) == 0:
                await ctx.send('`echale agua al caparazon de la tortuga, ole!`', file=discord.File(chan_plot(), filename='ole.png'))
            else:
                await ctx.send('`echale agua al caparazon de la tortuga, ole!`', file=discord.File(chan_plot(int(args[0])), filename='ole.png'))
        except:
            await ctx.send('`retrasado`')
            raise

@bot.command()
async def chans(ctx, *args):
    if ctx.message.channel.name == 'otro':
        try:
            if len(args) == 0:
                await ctx.send('`'+show_chan_sampling()+'`')
            else:
                await ctx.send('`'+show_chan_sampling(int(args[0]))+'`')
        except:
            await ctx.send('`mongolic@ maric@`')

@bot.command()
async def dice(ctx, *args):
    if ctx.message.channel.name in ('otro', 'juegos'):
        try:
            if len(args) == 1:
                await ctx.send('`['+str(random.randint(1, int(args[0])))+']`')
            else:
                dice = [random.randint(1, int(args[0])) for x in range(int(args[1]))]
                await ctx.send('`'+str(dice)+'`')
        except:
            await ctx.send('`'+str(random.randint(1, 6))+'`')

@bot.command()
async def calc(ctx, *args):
    if ctx.message.channel.name == 'otro':
        try:
            await ctx.send('`{}`'.format(currency.calc(''.join(args))))
        except Exception as e:
            await ctx.send('`mongolic@`')
            raise e

@bot.command()
async def rolelock(ctx, *args):
    author_roles = ctx.author.roles
    if (any([role.permissions.is_superset(discord.Permissions(268435456))
             for role in author_roles]) or
        ctx.guild.owner == ctx.author):
        try:
            role_id = int(re.search('\d+', args[1]).group(0))
            member_id = int(re.search('\d+', args[2]).group(0))
        except:
            await ctx.send('`mogolico`')
            return
        role = ctx.guild.get_role(role_id)
        member = ctx.guild.get_member(member_id)
        if role and member:
            if os.path.exists(settings.autoroles_file):
                with open(settings.autoroles_file) as f:
                    autoroles = json.loads(f.read())
            else:
                autoroles = []
            has_autorole = any(autorole for autorole in autoroles
                               if role_id == autorole['role_id'] and
                                  member_id == autorole['member_id'] and
                                  ctx.guild.id == autorole['guild_id'])
            if args[0] == 'add':
                if not has_autorole:
                    autoroles.append({'name': str(member),
                                      'role_id': role_id,
                                      'member_id': member_id,
                                      'guild_id': ctx.guild.id,})
                    with open(settings.autoroles_file, 'w') as f:
                        f.write(json.dumps(autoroles, indent=4))
                    await member.add_roles(role)
                    await ctx.send('`added {} to {}`'.format(member, role))
                else:
                    await ctx.send('`{} had {} rolelock`'.format(member, role))
            elif args[0] == 'remove':
                if has_autorole:
                    autoroles = list(autorole for autorole in autoroles if
                                     not (role_id == autorole['role_id'] and
                                          member_id == autorole['member_id'] and
                                          ctx.guild.id == autorole['guild_id']))
                    with open(settings.autoroles_file, 'w') as f:
                        f.write(json.dumps(autoroles, indent=4))
                    await member.remove_roles(role)
                    await ctx.send('`{} removed from {}`'.format(member, role))
                else:
                    await ctx.send('`{} didn\'t have {} rolelock`'.format(member, role))
            else:
                await ctx.send('`mogolico`')
        else:
            print('role and member: {} and {}'.format(role, member))
            await ctx.send('`mogolico`')
    else:
        await ctx.send('`mogolico`')

@bot.command()
async def echo(ctx, *args):
    if ctx.author.id != 427560696243552256:
        await ctx.send(str(' '.join(args)))

@bot.command()
async def dolar(ctx, arg):
    if ctx.message.channel.name == 'otro':
        if arg == 'btc':
            btc_price_url = 'https://coinbase.com/api/v1/prices/spot_rate'
            localbtc_ticker_url ='https://localbitcoins.com/bitcoinaverage/ticker-all-currencies/'

            try:
                btc_price_r = requests.get(btc_price_url)
                localbtc_ticker_r  = requests.get(localbtc_ticker_url)
            except:
                message = 'no disponible'
            else:
                usdbtc = 1/currency.btc()

                global PRECIO_DOLAR
                
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

                ts = ['avg_12h', 'avg_6h', 'avg_1h', 'avg_24h']
                for t in ts:
                    try:
                        PRECIO_DOLAR = float(localbtc_ticker_r.json()['VES'][t])/float(usdbtc)
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

async def sample_chans():
    await bot.wait_until_ready()
    while not bot.is_closed():
        if not os.path.exists('chan_sample.json'):
            sample = []
        else:
            with open('chan_sample.json') as f:
                sample = json.loads(f.read())

        arepa = requests.get('https://8ch.net/arepa/index.html')
        match = re.findall('\<a class=\"post_no\" onclick.*?\>(\d+)\</a\>', arepa.text)
        arepa_newest = max([int(x) for x in match])
        
        ve = requests.get('https://www.hispachan.org/ve/')
        match = re.findall('\<a class=\"reflink2\" title=\"Responder a este post\".*?\>(\d+)\</a\>', ve.text)
        ve_newest = max([int(x) for x in match])

        sample.append({'timestamp': str(datetime.datetime.now()),
                       'count': {'arepa': arepa_newest,
                                 've': ve_newest}})

        with open('chan_sample.json', 'w') as f:
            f.write(json.dumps(sample))
        await asyncio.sleep(CHECK_THREAD_TIME)

async def read():
    while True:
        message = input()
        channel = bot.get_channel(482333951868928006)
        await channel.send(message)
        
@bot.event
async def on_ready():
    bot.loop.create_task(new_eightch_threads())
    bot.loop.create_task(sample_chans())
#    bot.loop.create_task(read())

def log(message):
    timestamp = str(datetime.datetime.now())
    for a in message.attachments:
        filename = '{} {}'.format(timestamp, a.filename)
        try:
            r = requests.get(a.url, stream=True)
        except Exception as e:
            logging.error(e)
        else:
            with open(os.path.join(settings.media_folder, filename), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

    urls = set(re.findall('https?://\S*', message.content))
    for url in urls:
        filename = '{} URL {}'.format(timestamp, url.replace('/', '_'))
        try:
            r = requests.get(url, stream=True)
        except Exception as e:
            logging.error(e)
        else:
            with open(os.path.join(settings.media_folder, filename), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

    attachments = ', '.join([a.filename for a in message.attachments])
    if message.attachments:
        m = '{} - {} - {} ({}): {}\n'.format(timestamp, message.channel,
                                             message.author, attachments,
                                             message.clean_content)
    else:
        m = '{} - {} - {}: {}\n'.format(timestamp, message.channel,
                                        message.author, message.clean_content)
    with open('chat.log', 'a', encoding='utf8') as f:
        f.write(m)

@bot.event
async def on_member_join(member):
    with open(settings.autoroles_file) as f:
        autoroles = json.loads(f.read())
        for autorole in autoroles:
            role = member.guild.get_role(autorole['role_id'])
            if (role and member.id == autorole['member_id'] and
                member.guild.id == autorole['guild_id']):
                print('added {} to {}'.format(member, role))
                await member.add_roles(role)
    

@bot.event
async def on_message(message):
    print(message.channel.id)
    if message.author != bot.user:
        if 'colomb' in message.content.casefold():
            await message.channel.send('malditos colombianos')
#        elif 'toddy' in message.content.casefold():
#            await message.channel.send(file=discord.File('toddy.png', filename='toddy.png'))
        if message.channel.name == 'otro':
            MAGIC_WORDS = '^toddy,? ¿?cu(a|á)nto (cuestan|valen|cuesta|vale|sale|salen)'
            if re.search(MAGIC_WORDS, message.content.casefold()):
                query = re.sub('^{} (unas|unos|una|un|el|los|las|la)?'.format(MAGIC_WORDS), '', message.content.casefold())
                query = re.sub('\W*$', '', query)
                if re.search('m(á|a)s car(a|o)$', query):
                    query = re.sub('m(á|a)s car(a|o)$', '', query)
                    sort = 'desc'
                elif re.search('m(á|a)s barat(a|o)$', query):
                    query = re.sub('m(á|a)s barat(a|o)$', '', query)
                    sort = 'asc'
                else:
                    sort = None
                query = query.lstrip().rstrip()
                msg = precio(query, sort)
                await message.channel.send(msg)
        await bot.process_commands(message)
#    log(message)


bot.run(settings.token)
