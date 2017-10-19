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

#. Download the current LTS (long-term support) Version of Ubuntu Server from the `Ubuntu Website <https://www.ubuntu.com/download/server/>`_
   
#. Install the operating system on a suitable network capable physical server or virtual machine 
   Follow the self guided installation instructions for Ubuntu selecting the manual package selection option
   
   .. image:: /_static/ubuntu_package_selection.jpg

Optional: Install OpenSSH
~~~~~~~~~~~~~~~~~~~~~~~~~

If you intend to work on the installation remotely (as in a virtual machine environment) it will be beneficial
to install OpenSSH and set a static IP. Skip this section if you don't require remote SSH access.
   
* Install Open SSH Server and Client
   ``sudo apt-get install openssh-server openssh-client``

* Determine the current IP address of the computer by running ``ifconfig`` document the IP address, netmask, and gateway information.

* Set Static IP
   ``sudo nano /etc/network/interfaces``

Your interfaces file should look similar to the following:

| ``auto eth0``

| ``iface eth0 inet static``  
| ``address yourIPaddress``   
| ``netmask 255.255.255.0``  
| ``gateway yourGateway``

.. note:: Unless you receive a Static External IP from your internet service provider this will be a completely local server, only accessible by computers on the same local network (like an office building)

   
Installing Necessary Packages
-----------------------------

In order to run BMON on a local web server you must first install some required packages

| **SQL Server & Associated Packages**
| ``sudo apt-get install mysql-server``
| ``mysql_secure_installation``
| ``sudo apt-get install php php-mysql``

| **Python Dependencies**
| ``sudo apt-get install build-essential checkinstall``
| ``sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev``

| **Python**
| ``cd /usr/src``
| ``sudo wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz``
| ``sudo tar xzf Python-2.7.13.tgz``
| ``sudo rm -rf Python-2.7.13.tgz``
| ``cd Python-2.7.13/``
| ``sudo ./configure``
| ``sudo make altinstall``
   
| **Python Pip & Python Dev** 
| ``cd $home``
| ``sudo apt-get install python-pip``
| ``pip install --upgrade pip``
| ``sudo apt-get install python-dev``

Installing the Virtual Environment
-----------------------------------
It is assumed we are working from within our $home directory

| **Virtualenv & Virtualenvwrapper**
| ``sudo pip install virtualenv virtualenvwrapper``

| **Adjust your .bashrc file to incorporate the virtual environment variables**
| ``echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc``
| ``echo "export WORKON_HOME=~/Env" >> ~/.bashrc``
| ``source ~/.bashrc`` 

| **Create your virtual environment**
| ``mkvirtualenv bmon``

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

cd bmon

pip install -r requirements.txt

Creating BMON Settings File
---------------------------

cd bmon (you should be in bmon/bmon now)

Django requires a ``settings.py`` file to provide essential information for running a project. We will start with a sample settings file and make necessary changes.

| Move to the $home/bmon/bmon directory (yes, the bmon folder inside the bmon folder) and create a settings.py file from the sample located there:
| ``sudo cp settings_example.py settings.py``

| Open ``settings.py`` in an editor, e.g. ``sudo nano settings.py``. Each one of the settings is documented within the file. Examine each setting carefully for any needed changes.

| In this example, we modify the following attributes:
| ``BMSAPP_STORE_KEY`` - per the settings file, visit https://bms.ahfc.us/make-store-key to generate a key
| ``BMSAPP_TITLE_TEXT`` - purely cosmetic, change XYZ to the name of your organization/facility/etc.
| ``BMSAPP_HEADER`` - purely cosmetic, change XYZ to the name of your organization/facility/etc.
| ``ALLOWED_HOSTS`` - change to the server IP address or the URL depending on your setup ex. ['172.20.127.167'] (brackets and single quotes necessary)
| ``SECRET_KEY`` - per the settings file, visit https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-SECRET_KEY to generate a key 
| ``BMSAPP_STATIC_APP_NAME`` - indicate the full path of your project to the first level, then add static ex. /home/cchrc/bmon/static

Configuring the Manage.py file
------------------------------
Unlike in the :ref:`how-to-install-BMON-on-a-web-server` documentation, we need to modify the manage.py file to point to the correct python location

type ``which python`` and note the path ex. /home/cchrc/Env/bmon/bin/python

``cd $home/bmon`` or ``cd ..`` if you just finished the prior step.

| Modify manage.py
| ``sudo nano manage.py``
| Change #!/usr/local/bin/python2.7 to whatever path came up when you typed ``which python``

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

Now, end your virtual session by typing ``deactivate``


Configuring the Webserver
-------------------------
   
.. note:: The steps in this section are patterned after the general instructions from Digital Ocean's `How To Serve Django Applications with uWSGI and Nginx on Ubuntu 16.04 <https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-uwsgi-and-nginx-on-ubuntu-16-04/>`_

It is very important that you are no longer in the virtual session, make sure you've typed ``deactivate`` and your prompt has changed before proceeding

| **Install UWSGI**
| ``sudo pip install uwsgi``

| ``sudo mkdir -p /etc/uwsgi/sites``

| ``sudo nano /etc/uwsgi/sites/bmon.ini``

*example ini file*

----------------------

| [uwsgi]

| master = true
| processes = 5

| socket = /run/uwsgi/bmon.sock

| chmod-socket = 664
| chown-socket = cchrc:www-data
| home = /home/cchrc/Env/bmon

| chdir = /home/cchrc/bmon

| pythonpath = /home/cchrc/Env/bmon

| wsgi-file = /home/cchrc/bmon/bmon/wsgi.py
| vacuum = true

----------------------

Explanation:

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

| [Service]
| ExecStartPre=/bin/bash -c 'mkdir -p /run/uwsgi; chown cchrc:www-data /run/uwsgi'
| ExecStart=/usr/local/bin/uwsgi --emperor /etc/uwsgi/sites
| Restart=always
| KillSignal=SIGQUIT
| Type=notify
| NotifyAccess=all

| [Install]
| WantedBy=multi-user.target

----------------------

| The only portion of the service file that needs to be modified in your installation is
| ``ExecStartPre=/bin/bash -c 'mkdir -p /run/uwsgi; chown cchrc:www-data /run/uwsgi'``
where chown should indicate YOURUSERNAME:www-data


| **Install NGINX**

| ``sudo apt-get install nginx``

| ``sudo nano /etc/nginx/sites-available/bmon``

*example bmon settings file*

----------------------

| server {
|     listen 80;
|     server_name 172.20.127.167;
| 
|     location = /favicon.ico { access_log off; log_not_found off; }
|     location /static/ {
|         root /home/cchrc/bmon;
|     }
| 
|     location / {
|         include         uwsgi_params;
|         uwsgi_pass      unix:/run/uwsgi/bmon.sock;
|     }
| }

----------------------

The only portion of this file that needs to be changed is ``server_name`` which should be changed to either your server IP address or URL

| Enable the Site
| ``sudo ln -s /etc/nginx/sites-available/bmon /etc/nginx/sites-enabled``

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

Fire Up the Server
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

    */5 * * * * ~/webapps/bmon_django/bmon/manage.py runscript main_cron > /dev/null 2>&1

This cron job: 

* creates calculated reading values and stores Internet weather data in the reading database every half hour
* checks for active Alert Conditions every five minutes 
* creates a daily status line in the log file indicating how many sensor readings were stored in the database during the past day (viewable by browsing to ``<Domain URL>/show_log``) 
* creates a backup of the main Django database every day, and 
* creates a backup of the reading database every three days
