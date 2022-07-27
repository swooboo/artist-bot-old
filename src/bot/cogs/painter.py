import base64
import io
import logging
import discord
from discord.ext import commands
from discord.ext.commands.bot import Context
from aiohttp import ClientConnectorError

from ..utils.craiyon import generate_images_base64, PROMPT_CONCURRENT_LIMIT, prompt_limit_semaphore, \
    RequestsLimitExceededException, CraiyonRequestFailedException
from ..utils.imageconvert import combine_base64_images, ZeroImagesReceivedException


# @package painter
#
# Collection of miscellaneous helpers.
#

class Painter(commands.Cog):
    """
    A creative painter
    """

    @commands.command(name='draw', help='Draw a requested image')
    async def draw(self, ctx: Context, *prompt_words):
        """!
        Draws a requested image

        @param ctx Context of the message
        @param prompt_words The subject to draw
        """

        logging.info(f"Received !prompt from author {ctx.author}")
        prompt_text = ' '.join(prompt_words)
        ack_message = await ctx.send(f"{ctx.author.mention}, drawing {prompt_text}")
        try:
            image_base64 = await get_image_base64_from_prompt(prompt_text)
        except RequestsLimitExceededException:
            logging.warning(f'Limit exception raised for prompt "{prompt_text}", dropped')
            await ack_message.edit(content=f'{ack_message.content}... Limit reached, sorry.')
            return
        except CraiyonRequestFailedException:
            await ack_message.edit(content=f'{ack_message.content}... Errors while drawing, request failed.')
            return
        except ZeroImagesReceivedException:
            await ack_message.edit(content=f'{ack_message.content}... Errors while drawing, zero images received.')
            return
        except ClientConnectorError:
            await ack_message.edit(content=f'{ack_message.content}... Errors while drawing, client failed.')
            return

        attachment_file, embed = prepare_file_and_embed(image_base64, prompt_text)
        logging.info(f"Sending embed triggered by author {ctx.author}")
        await ctx.send(file=attachment_file, embed=embed)
        await ack_message.edit(content=f'{ack_message.content}... Et voilà!')

    @commands.command(name='stats', help='Show statistics')
    async def stats(self, ctx: Context):
        """!
        Shows statistics

        @param ctx Context of the message
        """

        logging.info(f"Received !stats from author {ctx.author}")
        stats_dict = {
            'status': 'online',
            'queries being executed': PROMPT_CONCURRENT_LIMIT - prompt_limit_semaphore._value,
            'max concurrent queries': PROMPT_CONCURRENT_LIMIT
        }
        stats_lines = list(f'{k}: {v}' for k, v in stats_dict.items())
        stats_lines.insert(0, '```')
        stats_lines.append('```')
        await ctx.send('\n'.join(stats_lines))


def prepare_file_and_embed(image_base64, prompt_text):
    embed = discord.Embed(title=prompt_text,
                          color=discord.colour.Color.dark_gold())
    embed.set_footer(text='Powered by craiyon.com')
    attachment_file = discord.File(io.BytesIO(base64.b64decode(image_base64)), filename='craiyon.jpg')
    embed.set_image(url='attachment://craiyon.jpg')
    return attachment_file, embed


async def get_image_base64_from_prompt(prompt_text: str):
    craiyon_response = await generate_images_base64(prompt_text)
    images_base64 = craiyon_response['images']
    return combine_base64_images(images_base64)


def setup(bot):
    bot.add_cog(Painter(bot))
