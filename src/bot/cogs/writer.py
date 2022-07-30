import logging
import random

import discord
from discord.ext import commands
from discord.ext.commands.bot import Context
import aiohttp

import src.bot.environment as env

# @package writer
#
# Collection of miscellaneous helpers.
#

QUOTES_CATEGORIES = ['age', 'science', 'success', 'time', 'travel', 'wisdom', 'alone', 'art', 'attitude', 'courage',
                     'culture', 'dreams', 'friendship', 'happiness', 'hope', 'humour', 'imagination', 'inspirational',
                     'life', 'motivational', 'nature', 'philosophy', 'poetry', 'popular', 'psychology']


class Writer(commands.Cog):
    """
    A creative writer
    """

    @commands.command(name='quote', help='Get a random quote in one of the categories, humor by default. Available '
                                         'categories: ' + ', '.join(QUOTES_CATEGORIES) + '.')
    async def quote(self, ctx: Context, category: str = 'humour') -> None:
        """!
        Posts a random quote from a category

        @param ctx Context of the message
        @param category The quotes category
        """

        logging.info(f"Received !quote from author {ctx.author} within the {category} category")
        if category not in QUOTES_CATEGORIES:
            await ctx.send(f'Category "{category}" is invalid. Post `{env.PREFIX}help writer` for the list of all the '
                           'available categories')
            return

        try:
            quote, author = await get_random_quote(category)
        except RandomQuoteRequestFailed:
            logging.exception('Querying for quotes failed')
            await ctx.send('I can\'t remember any quotes right now. My memory isn\'t what '
                           'it used to be, not since the accident...')
            return

        quote_embed = prepare_quote_embed(quote, author)
        await ctx.send(embed=quote_embed)


def prepare_quote_embed(quote: str, author: str) -> discord.Embed:
    embed = discord.Embed(description=f'**{quote}**',
                          color=discord.colour.Color.dark_gold())
    embed.set_footer(text=author)
    return embed


async def get_random_quote(category: str = 'humour') -> (str, str):
    quotes = [{'text': '"I don\'t know"', 'author': 'Nobody'}]
    query_headers = {'X-RapidAPI-Key': "456f319919msh7915cb535acbbafp114225jsn0dbe3a1454fa",
                     'X-RapidAPI-Host': "quotes-villa.p.rapidapi.com"}
    async with aiohttp.request(method='GET', url=f'https://quotes-villa.p.rapidapi.com/quotes/{category}',
                               headers=query_headers) as response:
        if response.status == 200:
            logging.info(f'Querying for quotes in the {category} category complete, got status: {response.status}')
            quotes = await response.json()
        else:
            logging.error(f'Querying for quotes in the {category}, got status: {response.status}')
            raise RandomQuoteRequestFailed(response.status, category)
    random_result = random.choice(quotes)
    quote_strings = [random_result['text'], random_result['author']]
    quote, author = [s.strip(' ,') for s in quote_strings]
    return quote, author


class RandomQuoteRequestFailed(Exception):
    def __init__(self, status, category):
        super().__init__(f'Querying quotes API for category {category} failed with status {status}')


def setup(bot):
    bot.add_cog(Writer(bot))
