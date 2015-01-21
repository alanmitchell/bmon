#!/bin/bash

# Install the Python packages necessary for the BMON application.
# Some of this install script is specific to the Webfaction hosting
# service.

# install the pip installer package
easy_install-2.7 pip

# need to install this later version of numpy and ignore the numpy
# version that is present already with webfaction.  This has to be 
# done prior to the requirments file, as installation of numexpr in
# that requirements package errors out otherwise.
pip install -I --user numpy==1.9.1

# install all the packages in the requirements.txt file
pip install --user -r requirements.txt

# manual install of the metar libary, pulling the package from the
# analysisnorth.com site.  This
wget http://analysisnorth.com/packages/metar-1.4.0.tar.gz
tar xzf metar-1.4.0.tar.gz
cd metar-1.4.0
PYTHONPATH=$HOME/lib/python2.7 python2.7 setup.py install --install-lib=$HOME/lib/python2.7 --install-scripts=$HOME/bin --install-data=$HOME/lib/python2.7
cd ..
rm -rf metar-1.4.0
rm metar-1.4.0.tar.gz
