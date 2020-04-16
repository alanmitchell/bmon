.. _how-to-install-BMON-locally:

How to Install BMON on a Local Web Server
=========================================

This document describes how to alternatively install the BMON application on a local web
server. The specific steps shown here apply to installation on a locally
housed Linux server running NGINX and UWSGI. This installation process has been tested and reproduced
multiple times in a test environment, however your mileage may vary. There are many ways to 
configure a web server, this is just a method that worked for us - install at your own
risk. 

The assumption here is that BMON will be installed on a server running
the `Linux operating system <https://www.ubuntu.com/download/server/>`_.

The skills needed for installation are primarily:

*  Linux command line skills - it is assumed you are familiar so explanations of basic linux command line operations are not included in this documentation.
*  Some experience with `Python <https://www.python.org/>`_ and the `Django
   web framework <https://www.djangoproject.com/>`_ would be helpful,
   as the BMON application is a Python application built using the
   Django web framework. If you are using the Wefaction hosting
   services, these skills are not absolutely necessary, as step-by-step
   installation instructions for that hosting service are detailed below.
   If you are *not* using the Webfaction hosting service, more Django
   and Python skills will be required, as the instructions below will
   need to be modified to fit your configuration.
*  Some knowledge of the `Git version control
   system <http://git-scm.com/>`_ would be helpful.
   
   
Install and Configure the Server Operating System
--------------------------------------------------

#. Download the current LTS (long-term support) Version of Ubuntu Server from the `Ubuntu Website <https://www.ubuntu.com/download/server/>`_. This documentation was written for Ubuntu Server 18.04.2 LTS.
   
#. Install the operating system on a suitable network capable physical server or virtual machine 
   Follow the self guided installation instructions for Ubuntu, optionally installing OpenSSH for remote access.
   
#. Run updates using ``sudo apt-get update`` and ``sudo apt-get upgrade``

 
Installing Necessary Packages
-----------------------------

In order to run BMON on a local web server you must first install some required packages

| **Python Dependencies**
| ``sudo apt install build-essential checkinstall``
| ``sudo apt-get install -y build-essential checkinstall libreadline-gplv2-dev python3.7 python3.7-dev libpython3.7-dev uwsgi uwsgi-src uuid-dev libcap-dev libpcre3-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev zlib1g-dev openssl libffi-dev python3-dev python3-setuptools wget``


| **SQL Server**
| ``sudo apt-get install mysql-server``
| ``sudo mysql_secure_installation``
   
| **Python Pip** 
| ``cd $home``
| ``sudo apt-get install python3-pip``
| ``sudo -H pip3 install --upgrade pip``


Installing the Virtual Environment
-----------------------------------
It is assumed we are working from within our $home directory

| **Virtualenv & Virtualenvwrapper**
| ``sudo -H pip3 install virtualenv virtualenvwrapper``

| **Adjust your .bashrc file to incorporate the virtual environment variables**
You may need to run ``whereis virtualenvwrapper.sh`` and document the path.

| ``sudo nano ~/.bashrc``

|   Add the following to the end of the file:
|	``export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3``
|	``export WORKON_HOME=~/Env``
|	``source /usr/local/bin/virtualenvwrapper.sh``
|	``PYTHON=python3.7``

|   Save the file and then run:
| ``source ~/.bashrc`` 

If the parameters added to your bashrc are correct - virtualenvwrapper scripts will be created like this:

| virtualenvwrapper.user_scripts creating /home/cchrc/Env/premkproject
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/postmkproject
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/initialize
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/premkvirtualenv
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/postmkvirtualenv
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/prermvirtualenv
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/postrmvirtualenv
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/predeactivate
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/postdeactivate
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/preactivate
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/postactivate
| virtualenvwrapper.user_scripts creating /home/cchrc/Env/get_env_details

| **Create your virtual environment**
| ``cd home``
| ``mkvirtualenv bmon -p python3.7``

You will know you are successful if an Env directory is created within your home directory.
Once you make your virtual environment, while it's active, your prompt will change
to indicate you are working in the virtual environment, below is an example of how it will look

.. image:: /_static/environments.jpg

.. note:: To exit your virtual environment type ``deactivate`` to resume working in your virtual environment type ``workon bmon`` for the instructions below continue working in your virtual environment until instructed to exit.

Installing the Required Python Packages & BMON Project
------------------------------------------------------

| **Install BMON & Required Packages**

| ``sudo git clone https://github.com/alanmitchell/bmon.git``

A directory named bmon will be created in your $home directory

| ``cd bmon``

| ``pip3 install -r requirements.txt``

Creating BMON Settings File
---------------------------

``cd bmon`` (you should be in bmon/bmon now)

Django requires a ``settings.py`` file to provide essential information for running a project. We will start with a sample settings file and make necessary changes.

| Move to the $home/bmon/bmon directory (yes, the bmon folder inside the bmon folder) and create a settings.py file from the sample located there:
| ``sudo cp settings_example.py settings.py``

| Open ``settings.py`` in an editor, e.g. ``sudo nano settings.py``. Each one of the settings is documented within the file. Examine each setting carefully for any needed changes.

| In this example, we modify the following attributes:
| ``BMSAPP_STORE_KEY`` - per the settings file, visit https://bms.ahfc.us/make-store-key to generate a key
| ``BMSAPP_TITLE_TEXT`` - purely cosmetic, change XYZ to the name of your organization/facility/etc.
| ``BMSAPP_HEADER`` - purely cosmetic, change XYZ to the name of your organization/facility/etc.
| ``ALLOWED_HOSTS`` - change to the server IP address or the URL depending on your setup ex. ['172.20.127.167'] (brackets and single quotes necessary)
| ``SECRET_KEY`` - per the settings file, visit https://www.miniwebtool.com/django-secret-key-generator/ to generate a key 
| ``BMSAPP_STATIC_APP_NAME`` - indicate the full path of your project to the first level, then add static ex. /home/cchrc/bmon/static

Configuring the Manage.py file
------------------------------
Unlike in the :ref:`how-to-install-BMON-on-a-web-server` documentation, we need to modify the manage.py file to point to the correct python location

type ``which python3.7`` and note the path ex. /home/cchrc/Env/bmon/bin/python3.7

``cd $home/bmon`` or ``cd ..`` if you just finished the prior step.

| Modify manage.py
| ``sudo nano manage.py``
| Change #!/usr/local/bin/python3.7 to whatever path came up when you typed ``which python``, but the line must begin with
| ``#!`` before the path to the Python executable.

| Test the manage.py file for errors 
| ``sudo ./manage.py check``

You're looking for System check identified no issues (0 silenced)
If you get a permission denied error make sure your path is typed correctly in the manage.py file

Create the Django Database, Install Initial Data, and Prepare Static Files
--------------------------------------------------------------------------

| Create the Django database file by executing:
| ``sudo ./manage.py migrate``

| Some initial data for common sensor units, sensor categories, and a
   sample building and sensor should be loaded into the database by:
| ``sudo ./manage.py loaddata init_data.yaml``

| Copy the static files (images, stylesheets, JavaScript files, etc.)
   into the folder where they will be served by the Static Application
   you created. Do this by executing:
| ``sudo ./manage.py collectstatic``

| In order to use the Admin site for setting up sensors and buildings,
   we need to create an admin user. To do this, execute:
| ``sudo ./manage.py createsuperuser``

Enter your desired username, email, and password to complete the
setup. The username and password created here will be the credentials
needed to log into the Admin side of the BMON site.

| Test the development server by running the following:
| ``sudo ./manage.py runserver SERVERIP OR URL:8000``

Then go to SERVERIP OR URL:8000 in your web browser and see if you see a poorly formatted version of BMON (the CSS doesn't load in development). End the test by pressing ``Ctl-C`` to kill the process 

Configuring the Webserver
-------------------------
   
.. note:: The steps in this section are patterned after the general instructions from Digital Ocean's `How To Serve Django Applications with uWSGI and Nginx on Ubuntu 18.04 <https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04>`_

.. note:: We are still working in the virtualenvironment

| **Install & Compile UWSGI**
| ``cd $home``
| ``sudo wget https://projects.unbit.it/downloads/uwsgi-latest.tar.gz``
| ``tar zxvf uwsgi-latest.tar.gz``
| ``sudo rm -rf uwsgi-latest.tar.gz``
| ``cd to the newly made uwsgi directory``
| ``python3.7 uwsgiconfig.py --build``
| ``make PROFILE=nolang``

Create the python 3.7 plugin

| ``PYTHON=python3.7 ./uwsgi --build-plugin "plugins/python python37"``

Link the file

| ``sudo ln -s /home/cchrc/[uwsgi directory]/uwsgi /usr/local/bin/uwsgi``

Now, end your virtual session by typing ``deactivate``


| ``sudo mkdir -p /etc/uwsgi/sites``

| ``sudo nano /etc/uwsgi/sites/bmon.ini``

*example ini file*

----------------------

| [uwsgi]
| plugins-dir = /home/cchrc/[uwsgi directory]
| plugin = python37
| 
| project = bmon
| uid = cchrc
| base = /home/%(uid)
| 
| chdir = %(base)/%(project)
| home = %(base)/Env/%(project)
| module = %(project).wsgi:application
| pythonpath = %(base)/Env/%(project)/bin/python3.7
| 
| master = true
| processes = 5
| 
| socket = /run/uwsgi/%(project).sock
| chown-socket = %(uid):www-data
| chmod-socket = 660

----------------------

Explanation:

| plugins-dir = the location of your uwsgi install
| plugin = tells uwsgi to use python 3.7 as default
| chown-socket = YOURUSERNAME:www-data
| home = /path/to/home/Env/bmon
| chdir = /path/to/project
| pythonpath = /path/to/home/Env/bmon
| wsgi-file = /path/to/home/bmon/bmon/wsgi.py


| **Create a Service File**
| ``sudo nano /etc/systemd/system/uwsgi.service``

*example service file*

----------------------

| [Unit]
| Description=uWSGI Emperor service
| 
| [Service]
| ExecStartPre=/bin/bash -c 'mkdir -p /run/uwsgi; chown cchrc:www-data /run/uwsgi'
| ExecStart=/usr/local/bin/uwsgi --emperor /etc/uwsgi/sites
| Restart=always
| KillSignal=SIGQUIT
| Type=notify
| NotifyAccess=all
| 
| [Install]
| WantedBy=multi-user.target

----------------------

| The only portion of the service file that needs to be modified in your installation is
| ``ExecStartPre=/bin/bash -c 'mkdir -p /run/uwsgi; chown cchrc:www-data /run/uwsgi'``
where chown should indicate YOURUSERNAME:www-data

``cd $home``


| **Install NGINX**

| ``sudo apt-get install nginx``

| ``sudo nano /etc/nginx/sites-available/bmon``

*example bmon settings file*

----------------------

| server {
| listen 80;
| server_name 172.20.127.197;
| 
| location = /favicon.ico { access_log off; log_not_found off; }
| location /static/ {
| root /home/cchrc/bmon;
| }
| 
| location / {
| include uwsgi_params;
| uwsgi_pass unix:/run/uwsgi/bmon.sock;
| }
| }


----------------------

The only portion of this file that needs to be changed is ``server_name`` which should be changed to either your server IP address or URL and ``root`` should reflect your own directory structure.

| Enable the Site
| ``sudo ln -s /etc/nginx/sites-available/bmon /etc/nginx/sites-enabled``

| Create a uwsgi run directory
| ``sudo mkdir /run/uwsgi``
| ``sudo chown -R cchrc:www-data /run/uwsgi``
| ``sudo chmod -R 774 /run/uwsgi``


| Change some owners and permissions to make sure the files are accessible 

| ``sudo chown -R cchrc:www-data /home/cchrc``
| ``sudo chmod -R 774 /home/cchrc/``

Here, you would substitute YOURUSERNAME where cchrc is and /your/home/path where /home/cchrc is

Create an override file (this was done to fix some errors)

| ``sudo mkdir /etc/systemd/system/nginx.service.d``

| ``sudo nano /etc/systemd/system/nginx.service.d/override.conf``

Put a space in the file and save

Change owners and permissions for the override file

| ``sudo chmod 666 /etc/systemd/system/nginx.service.d/override.conf``
| ``sudo chown cchrc:www-data /etc/systemd/system/nginx.service.d/override.conf``

| ``sudo printf "[Service]\nExecStartPost=/bin/sleep 0.1\n" > /etc/systemd/system/nginx.service.d/override.conf``

Start the Server
------------------

| ``sudo systemctl daemon-reload``
| ``sudo systemctl restart nginx``

| ``sudo nginx -t``
| you want to see the following 
| nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
| nginx: configuration file /etc/nginx/nginx.conf test is successful

| ``sudo systemctl start uwsgi``

To check the status of any process type the following: ``sudo systemctl status SERVICENAME`` (ex. nginx)

You should now be able to reach your project by going to its respective domain name or IP address from your preferred web browser.

| If you are unable to access the site through your web browser you can test by entering
| ``sudo uwsgi --http SERVERIP OR URL:8080 --home /home/cchrc/Env/bmon --chdir /home/cchrc/bmon -w bmon.wsgi``
and visiting the URL.
| reviewing the nginx error log may also help troubleshoot ``sudo tail -30 /var/log/nginx/error.log`` If you see messages about /run/uwsgi/bmon.sock failed (2: No such file or directory) while connecting to upstream it usually means you need to rerun the permission settings for the /run/uwsgi folder.

.. note:: change the IP address in the line above with either your server's ip address or URL specified in your configuration

If everything works, do the following to have nginx uwsgi start automatically

| ``sudo systemctl enable nginx``
| ``sudo systemctl enable uwsgi``


Cron Jobs
---------

One cron job is necessary for the BMON application. To edit the your
crontab file, execute ``crontab -e``. Then, add the following line to
the file:

::

    */5 * * * * cd /home/cchrc/bmon && ./manage.py runscript main_cron > /dev/null 2>&1

This cron job: 

* creates calculated reading values and stores Internet weather data in the reading database every half hour
* checks for active Alert Conditions every five minutes 
* creates a daily status line in the log file indicating how many sensor readings were stored in the database during the past day (viewable by browsing to ``<Domain URL>/show_log``) 
* creates a backup of the main Django database every day, and 
* creates a backup of the reading database every three days
