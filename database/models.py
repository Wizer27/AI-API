from sqlalchemy import Table,Column,Integer,String,MetaData,ARRAY
from sqlalchemy.dialects.postgresql import JSONB

metadata_obj = MetaData()

users_table = Table("users",
                    metadata_obj,
                    Column("username",String,primary_key=True),
                    Column("hash_psw",String),
                    Column("chats",JSONB)
                    )


