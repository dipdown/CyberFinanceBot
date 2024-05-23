import asyncio
import random
import time
import traceback
import aiohttp

from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from fake_useragent import UserAgent
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView
from urllib.parse import unquote, quote

from data import config
from utils.core import logger

headers = {
    'Accept': 'application/json',
    'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
    'Connection': 'keep-alive',
    'Origin': 'https://game.cyberfinance.xyz',
    'Referer': 'https://game.cyberfinance.xyz/',
    'Content-Type': 'application/json',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': UserAgent(os='android').random,
    'sec-ch-ua': '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123", "Microsoft Edge WebView2";v="123"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

class Cyber:
    def __init__(self, session_name: str, session_proxy: str | None = None):
        self.session_name: str = session_name
        self.session_proxy = session_proxy
        
        if session_proxy:
            proxy = Proxy.from_str(session_proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None
        self.tg_client = Client(name=session_name,
                                workdir=config.WORKDIR,
                                proxy=proxy_dict
                                )
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True)
    
    async def check_proxy(self, http_client: aiohttp.ClientSession) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as e:
            logger.error(f"Error checking proxy account {self.session_name}: {e}")
    
    async def start_farming(self):
        await self.tg_client.start()
        proxy_conn = ProxyConnector().from_url(self.session_proxy) if self.session_proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if self.session_proxy:
                await self.check_proxy(http_client=http_client)
            
            while True:
                try:
                    await asyncio.sleep(random.uniform(config.ACC_DELAY[0], config.ACC_DELAY[1]))
                    await self.login(http_client=http_client, proxy=self.session_proxy)
                    
                    while True:
                        try:
                            crack_time, balance = await self.check_claim(http_client=http_client)
                            current_time = time.time()
                            
                            await asyncio.sleep(random.uniform(config.TASK_DELAY[0], config.TASK_DELAY[1]))
                            await self.check_missions_and_complete(http_client=http_client)
                            
                            await asyncio.sleep(random.uniform(config.TASK_DELAY[0], config.TASK_DELAY[1]))
                            await self.check_boosts_and_upgrade(http_client=http_client, user_balance=balance)
                            
                            if crack_time is not None and crack_time > current_time:
                                logger.info(f"{self.session_name} | Sleeping. Next claim in: {(crack_time - current_time) / 60} mins.")
                                await asyncio.sleep(crack_time - current_time + 60)
                                await self.claim(http_client=http_client)
                            else:
                                logger.info(f"{self.session_name} | Time to claim.")
                                await asyncio.sleep(random.uniform(config.TASK_DELAY[0], config.TASK_DELAY[1]))
                                await self.claim(http_client=http_client)

                        except Exception as e:
                            logger.error(f"{self.session_name} | Error: {e}")
                            traceback.print_exc()
                except Exception as e:
                    logger.error(f"{self.session_name} | Error: {e}")
                    traceback.print_exc()

    async def login(self, http_client: aiohttp.ClientSession, proxy: str | None):
        tg_web_data: str = await self.get_tg_web_data(proxy)
        resp = await http_client.post("https://api.cyberfinance.xyz/api/v1/game/initdata/", json={'initData': tg_web_data})
        http_client.headers['Authorization'] = "Bearer " + (await resp.json(content_type=None))['message']['accessToken']

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict
        
        await self.tg_client.send_message(chat_id="CyberFinanceBot", text="/start cj10R25oTGhRNUViZEsmdT1yZWY==")

        web_view = await self.tg_client.invoke(RequestWebView(
            peer=await self.tg_client.resolve_peer('CyberFinanceBot'),
            bot=await self.tg_client.resolve_peer('CyberFinanceBot'),
            platform='android',
            from_bot_menu=False,
            url='https://game.cyberfinance.xyz/'
        ))

        auth_url = web_view.url
        tg_web_data: str = unquote(string=unquote(string=auth_url.split(sep='tgWebAppData=', maxsplit=1)[1].split(sep='&tgWebAppVersion',maxsplit=1)[0]))
        decoded_data = unquote(tg_web_data)

        json_start_index = decoded_data.find('user=') + len('user=')
        json_end_index = decoded_data.find('&auth_date')
        json_data_str = decoded_data[json_start_index:json_end_index]

        encoded_json_str = quote(json_data_str)
        tg_web_data = decoded_data.replace(json_data_str, encoded_json_str)

        return tg_web_data

    async def check_claim(self, http_client: aiohttp.ClientSession):
        resp = await http_client.get("https://api.cyberfinance.xyz/api/v1/game/mining/gamedata")
        resp_json = await resp.json(content_type=None)

        crack_time = resp_json.get("message", {}).get("miningData", {}).get("crackTime")
        balance = resp_json.get("message", {}).get("userData", {}).get("balance")

        return int(crack_time), int(balance)

    async def claim(self, http_client: aiohttp.ClientSession):
        resp = await http_client.get("https://api.cyberfinance.xyz/api/v1/mining/claim")
            
        if resp.status == 200 or resp.status == 201:
            resp_json = await resp.json(content_type=None)
            balance = resp_json.get("message", {}).get("userData", {}).get("balance")
                
            logger.success(f"Thread {self.session_name} | Reward received! Balance: {balance}")
        else:
            logger.error(f'{self.session_name} | Error: {resp.status}')

    async def check_missions_and_complete(self, http_client: aiohttp.ClientSession):
        try:
            logger.info(f'{self.session_name} | Checking missions')
            resp = await http_client.get('https://api.cyberfinance.xyz/api/v1/gametask/all')
            
            if resp.status == 200 or resp.status == 201:
                logger.info(f'{self.session_name} | Missions retrieved')
                data = await resp.json(content_type=None)
                for item in data['message']:
                    if not item['isCompleted'] and item['isActive']:
                        await self.complete_mission(http_client, item['uuid'])
            else:
                logger.error(f'{self.session_name} | Error retrieving missions: {resp.status}')
        except Exception as e:
            logger.error(f"{self.session_name} | Error: {e}")

    async def complete_mission(self, http_client: aiohttp.ClientSession, mission_uuid: str) -> dict:
        try:
            await asyncio.sleep(random.uniform(config.TASK_DELAY[0], config.TASK_DELAY[1]))
            resp = await http_client.patch(f'https://api.cyberfinance.xyz/api/v1/gametask/complete/{mission_uuid}')

            if resp.status == 200 or resp.status == 201:
                logger.info(f'{self.session_name} | Mission - {mission_uuid} completed')
                return await resp.json(content_type=None)
        except Exception as error:
            logger.error(f'{self.session_name} | Error completing mission: {error}')
    
    async def check_boosts_and_upgrade(self, http_client: aiohttp.ClientSession, user_balance: int):
        while True:
            try:
                logger.info(f'{self.session_name} | Checking boosts')
                resp = await http_client.get('https://api.cyberfinance.xyz/api/v1/mining/boost/info')

                if resp.status != 200 and resp.status != 201:
                    logger.error(f'{self.session_name} | Error getting boost info: {resp.status}')
                    break

                resp_json = await resp.json(content_type=None)
                hammer_price = resp_json.get("message", {}).get("hammerPrice")

                if int(user_balance) < int(hammer_price):
                    logger.info(f'{self.session_name} | Insufficient balance to buy hammer')
                    break

                await self.upgrade_hammer(http_client)
                user_balance -= int(hammer_price)

            except Exception as error:
                logger.error(f'{self.session_name} | Error getting boosts: {error}')
                break

    async def upgrade_hammer(self, http_client: aiohttp.ClientSession):
        try:
            await asyncio.sleep(random.uniform(config.TASK_DELAY[0], config.TASK_DELAY[1]))
            data = {'boostType': 'HAMMER'}
            resp = await http_client.post(url='https://api.cyberfinance.xyz/api/v1/mining/boost/apply', json=data)

            if resp.status != 200 and resp.status != 201:
                logger.error(f'{self.session_name} | Error buying hammer: {resp.status}')

            logger.info(f'{self.session_name} | Hammer bought')

        except Exception as error:
            logger.error(f'{self.session_name} | Error buying hammer: {error}')

async def start_farming(session_name: str, session_proxy: str | None = None) -> None:
    try:
        await Cyber(session_name=session_name, session_proxy=session_proxy).start_farming()

    except Exception as e:
        logger.error(f'{session_name} | {e}')
