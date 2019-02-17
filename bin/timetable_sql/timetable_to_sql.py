import os
from callback import callback, sqlite_connection_str
from timetable_parser.parser import  parser

# TODO: comand line interaction

def main():
    db_path = os.path.join(os.path.realpath('.'), 'test.db')
    c = callback(sqlite_connection_str(db_path))

    p = parser('http://poincare.matf.bg.ac.rs/~kmiljan/raspored/sve/index.html', True)
    p.parse(c)

    c.write_to_db()


if __name__ == '__main__':
    main()

