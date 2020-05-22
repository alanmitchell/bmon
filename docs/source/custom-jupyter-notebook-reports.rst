.. _custom-jupyter-notebook-reports:

How to Create Custom Jupyter Notebook Reports
=============================================

BMON has a top-level Menu Item titled "Energy Reports" (a BMON version of March 24, 2020
or later must be present, and the Energy Reports feature must be configured in the BMON
Settings file).  A number of special reports that analyze
the energy use of individual Buildings and analyze the energy use of Organziations are available to
show on this BMON page.  These reports satsify many analysis needs, but you also have the
ability to create your own custom report developed in a `Jupyter Notebook <https://jupyter.org/>`_ 
using the `Python Programming Language <https://www.python.org/>`_.  Note that these reports
fall under the "Energy Reports" menu item, your custom reports do not have to be related
to energy use; they can use any sensor data available in BMON and perform any form of data
analysis.

A Jupyter Notebook is a document that contains live programming code, equations, visualizations, and
formatted text.  Through use of the Python Programming language within the Notebook, data
from BMON can be acquired, analyzed, visualized and reported on.  The BMON Jupyter
Notebook reporting is structured to run these reports nightly and convert the output from
the report into an HTML document that is viewable through the "Energy Reports" menu item
in BMON.

The purpose of this How-To Guide is to show you how to create your own custom Jupyter Notebook
report that is automatically run nightly and viewable through BMON.  Your report can use
BMON data and data from anywhere on the Internet.  The Notebook has the full power of the Python
programming language available to it, so the range of available processing and data analysis tools
is very large.

To successfully create a custom report, you will need to have some basic level of skill with
the following tools and services:

* The Python programming language.

* Jupyter Notebooks

* `GitHub <https://github.com/>`_, a file sharing and version control system, which is used
  BMON to store the Jupyter Notebooks used for the creation of Energy Reports.

Note that BMON for a number of years has had a "Custom Reports" feature that allows you to 
combine a number of BMON Graphs onto one page, and have that page accessible as a Report.  This
feature is described here: :ref:`custom-reports`.  This feature is simpler to use than the Custom
Jupyter Report feature, but it lacks the power and flexibility offered by Jupyter Notebooks and
the Python programming language.

This guide provides some introductory text, but the bulk of the guide is in the form of
videos that walks through creation of a simple custom report.  These videos are available in the
last section of this page.

Prerequisites
-------------

This Guide assumes that your BMON system is already configured to run Energy Reports.  There are
a number of steps required to reach that point.  This Guide is *not* meant to provide detail
on those steps, but they are briefly listed here:

* Create a `GitHub <https://github.com/>`_ repository to hold the all of the Jupyter Notebooks
  that are used to create the Energy Reports, including your custom report.  `Here is a Sample
  GitHub Repository <https://github.com/alanmitchell/bmonreporter-templates>`_.

  * That repository must include a ``config.yaml`` configuration file in the root directory. This
    file indicates which BMON Servers the reports will run against, and it also specifies the
    formatting theme used for the Jupyter Notebooks.

* Ensure that the `bmonreporter <https://github.com/alanmitchell/bmonreporter>`_ software is setup
  to run nightly and that the configuration file for that software lists the above GitHub
  repository.  That software stores the created HTML reports in an Amazon AWS S3 bucket configured
  as a static website.  This website is accessed by BMON to display the created the reports.

* The ``ENERGY_REPORTS_URL`` setting in the ``settings.py`` file for your BMON server must have the URL
  of the AWS S3 static website.  Further, that settings file must have an ``Energy Reports`` item in the
  ``BMSAPP_NAV_LINKS`` setting.

Again, if your BMON install is already set up to run Energy Reports, none of the above needs
to be performed prior to creating a Custom Jupyter Notebook Report.

Creating the Custom Jupyter Notebook Report
-------------------------------------------

This section contains two videos to explain how the Custom Jupyter Report is created.  In
this first video, the difference between Building reports and Organization reports is
explained.  Also, the video explains where to store your Custom Juptyer Notebook file in the
GitHub repository.

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/NeeG9_4Pxl8" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

This next video walks through creation of an actual Jupyter Notebook report.  Please not some of the reference
links below the video for important resources. [*** Under Construction - Not Complete! ***]

.. raw:: html

    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
        <iframe src="https://www.youtube.com/embed/NeeG9_4Pxl8" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
    </div>

Here is some `documentation for the bmondata <https://github.com/alanmitchell/bmondata>`_ Python package,
which allows for easy access to BMON data from within your Jupyter Notebook (or any Python script for
that matter).  Example usage of the library is `shown here <http://web.analysisnorth.com.s3-us-west-2.amazonaws.com/bmondata/usage_examples.html>`_.

