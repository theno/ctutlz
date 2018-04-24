import aiohttp
import asyncio
import os
import os.path

import utlz
from utlz import flo

from ctutlz.utils.logger import logger


STEP_SIZE = 256


def check_get_entries_response(filename):
    '''
    Args:
        filename(str): e.g. get-entries-0-1023.json

    Return: True or False
    '''
    basename = os.path.basename(filename)
    start, end = basename.lstrip('get-entries-').rstrip('.json').split('-')
    start = int(start)
    end = int(end)

    get_entries_data = utlz.load_json(filename)
    entries = get_entries_data['entries']

    if not (len(entries) == end - start + 1):
        logger.warn(
            '%s get-entries-response too small '
            'expected size: %s, response_size: %s' % (filename,
                                                      end - start + 1,
                                                      len(entries)))
        os.remove(filename)
        return False

    return True


async def save_response(filename, response):
    with open(filename, mode='wb') as f_handle:
        # while True:
        #     chunk = await response.content.read(1024)
        #     if not chunk:
        #         break
        #     f_handle.write(chunk)
        data = await response.read()
        f_handle.write(data)


async def download(session, filename, url, params=None, skip_if_exists=True):
    file_exists = os.path.exists(filename)
    if not skip_if_exists or not file_exists:

        params_str = ''
        if params:
            params_str = ' ' + str(params)
        logger.verbose(flo('{url}{params_str} -> {filename}'))

        async with session.get(url, params=params) as response:
            assert response.status == 200, flo('expected: 200, got: '
                                               '{response.status}')
            await save_response(filename, response)
        if os.path.basename(filename).startswith('get-entries-'):
            check_get_entries_response(filename)


async def get_sth(session, ctlog_dir, ctlog_url):
    url = flo('{ctlog_url}ct/v1/get-sth')
    filename = os.path.join(ctlog_dir, 'get-sth.json')
    await download(session, filename, url, skip_if_exists=False)
    data = utlz.load_json(filename)
    return data['tree_size']


async def get_entries(session, ctlog_dir, ctlog_url, start, end):
    url = flo('{ctlog_url}ct/v1/get-entries')
    filename = os.path.join(ctlog_dir, flo('get-entries-{start}-{end}.json'))
    params = {'start': start, 'end': end}
    await download(session, filename, url, params=params, skip_if_exists=True)


def ctlog_dir_for(basedir, ctlog_uri):
    # eg. ctlog_dirname = 'ct1.digicert-ct.com_log'
    ctlog_dirname = ctlog_uri.rstrip('/').replace('/', '_')
    ctlog_dir = os.path.join(basedir, ctlog_dirname)
    return ctlog_dir


async def grabctlog_coroutine(session, ctlog_uri, basedir):
    ctlog_url = 'https://{}'.format(ctlog_uri)

    ctlog_dir = ctlog_dir_for(basedir, ctlog_uri)

    os.makedirs(ctlog_dir, exist_ok=True)

    tree_size = await get_sth(session, ctlog_dir, ctlog_url)
    logger.info(flo('{ctlog_url}: {tree_size}'))

    stop = tree_size
    step = STEP_SIZE
    # for start in range(stop - (step+3) - 100, stop, step):  # TODO DEVEL
    # for start in [0]:
    #    step = 2
    for start in range(0, stop, step):
        end = start + step - 1  # eg. end = 9999
        if end >= tree_size:
            end = tree_size - 1
        await get_entries(session, ctlog_dir, ctlog_url, start, end)


async def task_runner(loop, ctlog_uris, basedir):
    async with aiohttp.ClientSession(loop=loop) as session:
        tasks = [grabctlog_coroutine(session, uri, basedir)
                 for uri
                 in ctlog_uris]
        await asyncio.gather(*tasks)


def grab_ctlogs(uris, basedir):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task_runner(loop, uris, basedir))
