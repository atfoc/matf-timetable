from sqlalchemy import create_engine
from sqlalchemy.sql import Insert, select
from sqlalchemy.engine.result import  ResultProxy
from sqlalchemy import Table, Column,  VARCHAR, MetaData, Integer


engine = create_engine('sqlite:///:memory:', echo=True)

m = MetaData()

users = Table('users', m,
              Column('id', Integer, primary_key=True),
              Column('name', VARCHAR(10)),
              Column('fullname', VARCHAR(10)),
              Column('nickname', VARCHAR(10))
              )

m.create_all(engine)

ins = users.insert()
ins =  ins.values(name='hi')
ins.bind = engine
str(ins)

con = engine.connect()
r = con.execute(ins, name='cao', fullname='hi')

for i in con.execute(select([users])):
    print(i)
