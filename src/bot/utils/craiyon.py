import json
import logging
import aiohttp
from asyncio import Semaphore


CRAIYON_BACKEND_BASE_URL = 'https://backend.craiyon.com'
CRAIYON_GENERATE_RELATIVE_ENDPOINT = 'generate'
CRAIYON_GENERATE_ABSOLUTE_ENDPOINT = f'{CRAIYON_BACKEND_BASE_URL}/{CRAIYON_GENERATE_RELATIVE_ENDPOINT}'
PROMPT_CONCURRENT_LIMIT = 2
prompt_limit_semaphore = Semaphore(PROMPT_CONCURRENT_LIMIT)


async def _query_craiyon_api(prompt_text: str):
    logging.info(f'Querying Craiyon with prompt "{prompt_text}"')
    query_data = json.dumps({'prompt': prompt_text})
    query_headers = {'accept': 'application/json',
                     'cache-control': 'no-cache',
                     'content-type': 'application/json',
                     'pragma': 'no-cache'}
    async with aiohttp.request(method='POST', url=CRAIYON_GENERATE_ABSOLUTE_ENDPOINT, data=query_data, headers=query_headers) as response:
        if response.status == 200:
            logging.info(f'Querying Craiyon with prompt "{prompt_text}" complete, got status: {response.status}')
            return await response.json()
        else:
            logging.error(f'Querying Craiyon failed for prompt "{prompt_text}", got status: {response.status}')
            raise CraiyonRequestFailedException(response.status)


async def generate_images_base64(prompt_text: str):
    if prompt_limit_semaphore.locked():
        logging.warning(f'Prompt request limit reached, dropping request for prompt "{prompt_text}"')
        raise RequestsLimitExceededException(prompt_text)
    await prompt_limit_semaphore.acquire()
    try:
        return await _query_craiyon_api(prompt_text)
    finally:
        prompt_limit_semaphore.release()


class RequestsLimitExceededException(Exception):
    def __init__(self, prompt):
        super().__init__(f'Requests limit exceeded when drawing {prompt}, max concurrent queries is {PROMPT_CONCURRENT_LIMIT}')


class CraiyonRequestFailedException(Exception):
    def __init__(self, status):
        super().__init__(f'Querying Craiyon failed with status {status}')
