#!/bin/bash

# Install the Python packages necessary for the BMON application.
# Some of this install script is specific to the Webfaction hosting
# service.

# install the pip installer package
easy_install-2.7 pip

# need to install this later version of numpy and ignore the numpy
# version that is present already with webfaction.  This has to be 
# done prior to the requirments file, as installation of numexpr in
# that requirements file errors out otherwise.
pip install -I --user numpy==1.9.1

# install all the packages in the requirements.txt file
pip install --user -r requirements.txt
