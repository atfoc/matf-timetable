def mysql_connection_str(username: str, password: str, host: str, port: str,
                         db_name: str )->str:
    if port != '':
        port = f':{port}'
    if password != '':
        password = f':{password}'
    return f'mysql+pymysql://{username}{password}@{host}{port}/{db_name}'


def sqlite_connection_str(path: str)->str:
    """ :param path - absolute path to db or :memory: for in memory db"""
    return f'sqlite:///{path}'