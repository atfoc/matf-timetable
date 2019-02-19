from distutils.core import setup

install_requires = [
'beautifulsoup4==4.7.1',
'bs4==0.0.1',
'certifi==2018.11.29',
'chardet==3.0.4',
'idna==2.8',
'requests==2.21.0',
'soupsieve==1.7.3',
'urllib3==1.24.1'
]
setup(name='timetable_parser', version='0.1', packages=['timetable_parser'],
      install_requires=install_requires)