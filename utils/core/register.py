import pyrogram
from loguru import logger
from better_proxy import Proxy

from database import actions as db_actions

async def create_sessions():
    while True:
        session_name = input(
            '\nEnter session name (press Enter to exit): ')
        if not session_name:
            return

        api_string = input(
            'Enter api_id and api_hash in the format api_id:api_hash: ')

        api_parts = api_string.split(':')

        if len(api_parts) != 2:
            print("Invalid input format. Use the format api_id:api_hash.")
            break
        else:
            api_id = api_parts[0]
            api_hash = api_parts[1]

        while True:
            proxy_str: str = input('Enter Proxy (type://user:pass@ip:port // type://ip:port, to use without '
                                   'Proxy press Enter): ').replace('https://', 'http://')

            if proxy_str:
                try:
                    proxy: Proxy = Proxy.from_str(
                        proxy=proxy_str
                    )

                    proxy_dict: dict = {
                        'scheme': proxy.protocol,
                        'hostname': proxy.host,
                        'port': proxy.port,
                        'username': proxy.login,
                        'password': proxy.password
                    }

                except ValueError:
                    logger.error(
                        'Invalid Proxy specified, please try again')

                else:
                    break

            else:
                proxy: None = None
                proxy_dict: None = None
                break

        session: pyrogram.Client = pyrogram.Client(
            api_id=api_id,
            api_hash=api_hash,
            name=session_name,
            workdir='sessions/'
        )

        async with session:
            user_data = await session.get_me()

        logger.success(
            f'Successfully added session {user_data.username} | {user_data.first_name} {user_data.last_name}')

        await db_actions.add_session(session_name=session_name,
                                     session_proxy=proxy.as_url if proxy else '')
