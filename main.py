import asyncio
from os import listdir, mkdir
from os.path import exists, isdir

from utils.CyberFinance import start_farming
from utils.core import logger, create_sessions

from database import on_startup_database
from database import actions as db_actions

from utils.telegram import Accounts

start_text = """
Cyber Finance Bot

Select an action:

    1. Create session
    2. Run claimer
"""

async def main() -> None:
    await on_startup_database()
    user_action: int = int(input(start_text))
    
    match user_action:
        case 1:
            await create_sessions()

        case 2:
            accounts = await Accounts().get_accounts()
            tasks = []
            for account in accounts:
                session_proxy: str = await db_actions.get_session_proxy_by_name(session_name=account)

                tasks.append(asyncio.create_task(start_farming(session_name=account, session_proxy=session_proxy)))

            await asyncio.gather(*tasks)

        case _:
            print('Choose the correct number')

if __name__ == "__main__":
    if not exists(path='sessions'):
        mkdir(path='sessions')

    session_files: list[str] = [current_file[:-8] if current_file.endswith('.session')
                                else current_file for current_file in listdir(path='sessions')
                                if current_file.endswith('.session') or isdir(s=f'sessions/{current_file}')]

    logger.info(f'Found {len(session_files)} sessions')
    asyncio.get_event_loop().run_until_complete(main())
