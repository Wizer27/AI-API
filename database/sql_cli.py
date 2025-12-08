from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import Session,sessionmaker
from sqlalchemy import URL,create_engine,text
from config import conect,connect_login_data
import asyncio
from models import metadata_obj


sync_engine =  create_engine(
    url = conect(),
    echo = False,
    pool_size = 5,
    max_overflow=10,
)



#async def async_con():
    #async with async_engine.connect() as conn:
       # res = await conn.execute(text("SELECT VERSION()"))
        #print(f"{res.first()=}")

