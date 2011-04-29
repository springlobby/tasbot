from distutils.core import setup

setup(
    name='tasbot-spring',
    version='0.2.0',
    author=['Rene Milk','Andrea Piras','Tiziano'],
    author_email=['koshi@springlobby.info','braindamage@springlobby.info','']
    packages=['tasbot'] ,
    scripts=[],
    url='https://github.com/springlobby/tasbot',
    license='LICENSE.txt',
    description='extensible bot library for the spring server protocol',
    long_description=open('README.txt').read()
)