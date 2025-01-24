import aiohttp


async def fetch_xml(url: str, auth=None, timeout=10):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=auth, timeout=timeout) as response:
            return await response.text()
