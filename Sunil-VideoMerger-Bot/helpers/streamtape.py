# (c) @AbirHasan2005

import aiohttp
from configs import Config


async def streamtape_upload(file_path: str):
    try:
        async with aiohttp.ClientSession() as session:
            # Get upload URL
            async with session.get(f"https://api.streamtape.com/file/ul?login={Config.STREAMTAPE_API_USERNAME}&key={Config.STREAMTAPE_API_PASS}") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result['status'] == 200:
                        upload_url = result['result']['url']

                        # Upload file
                        with open(file_path, 'rb') as file:
                            data = aiohttp.FormData()
                            data.add_field('file1', file)

                            async with session.post(upload_url, data=data) as upload_resp:
                                if upload_resp.status == 200:
                                    upload_result = await upload_resp.json()
                                    if upload_result['status'] == 200:
                                        return upload_result['result']['url']
        return None
    except Exception as e:
        print(f"Streamtape upload error: {e}")
        return None
