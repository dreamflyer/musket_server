from setuptools import setup
import setuptools

setup(name='musket_server',
      version='0.1',
      description='musket_server',
      url='https://github.com/dreamflyer/musket_server',
      author='Dreamflyer',
      author_email='formyfiles3@gmail.com',
      license='MIT',
      packages=setuptools.find_packages(),
      include_package_data=True,
      install_requires=["musket_ml"],
      zip_safe=False,
      entry_points={
            'console_scripts': [
                  'musket_server = musket_server.main:main'
            ]
      })