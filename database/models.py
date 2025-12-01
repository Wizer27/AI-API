from sqlalchemy import Table,Column,Integer,String,MetaData


metadata_obj = MetaData()

users_table = Table("users",
                    metadata_obj,
                    Column("username",String,primary_key=True),
                    Column("hash_psw",String,primary_key = True)
                    )


