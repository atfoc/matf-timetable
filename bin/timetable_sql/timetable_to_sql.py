import os
import argparse as argp
import sys
import json
from callback import callback, sqlite_connection_str, mysql_connection_str
from timetable_parser.parser import  parser

# TODO: comand line interaction


def main():
    arg_parser = make_parser()


    namespace = arg_parser.parse_args(sys.argv[1:])
    if 'conf' in namespace:
        # mysql
        if namespace.conf is None and  (namespace.username is None or namespace.db_name is None):
            sys.exit('You must provide either conf or username and db_name at least')
        if namespace.conf is not None and (namespace.username is not None or namespace.db_name is not None):
            sys.exit('You must provide either conf or username and db_name at least')

        if namespace.conf is not None:
            with open(namespace.conf, 'r') as f:
                conf = json.load(f)
            if 'username' not in conf:
                sys.exit('Conf has to have username')
            namespace.username = conf['username']
            namespace.password = conf['password'] if 'password' in conf else ''
            namespace.host = conf['host'] if 'host' in conf else 'localhost'
            if 'db_name' not in conf:
                sys.exit('Conf has to have db_name')
            namespace.db_name = conf['db_name']
        db_str = mysql_connection_str(namespace.username, namespace.password, namespace.host,
                                      namespace.port, namespace.db_name)
    else:
        db_str = sqlite_connection_str(namespace.path)

    c = callback(db_str, namespace.prefix)

    p = parser('http://poincare.matf.bg.ac.rs/~kmiljan/raspored/sve/index.html', True)

    p.parse(c)

    c.write_to_db()

def make_parser()->argp.ArgumentParser:
    parser = argp.ArgumentParser()
    parser.add_argument('--prefix',  help='Prefix for each table in database', default='')

    sub_prasers = parser.add_subparsers()
    sqlite_parser = sub_prasers.add_parser('sqlite', help='Create sqlite database use sqlite -h for more detail')
    sqlite_parser.add_argument('path', help='Path where to crate database(including file) all parent dir have to exist')

    mysql_parser = sub_prasers.add_parser('mysql', help='Create mysql database use sqlite -h for more detail')
    mysql_parser.add_argument('--username', help='username for connecting to database')
    mysql_parser.add_argument('--db_name', help='name for database')
    mysql_parser.add_argument('--password', help='password for connecting to database', default='')
    mysql_parser.add_argument('--host', help='host where is the database', default='localhost')
    mysql_parser.add_argument('--port', help='post on host where is the database', default='')
    mysql_parser.add_argument('--conf', help='configuration file (json) containing info above')

    return parser


if __name__ == '__main__':
    main()

