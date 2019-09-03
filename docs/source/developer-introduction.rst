.. _developer-introduction:

Developer Introduction
======================

This section of the documentation is aimed at developers who wish to better
understand, perhaps modify, or to read data from the BMON software. The code
is thoroughly commented, but the documents described below are meant to
provide higher level documentation for the application.


:ref:`BMON Architecture <bmon-architecture>`
--------------------------------------------

This document describes the overall structure of the BMON application.
It also indicates the location of key elements of the BMON code and
describes generally the implementation approach.

:ref:`Writing Periodic Scripts <writing-periodic-scripts>`
----------------------------------------------------------

:ref:`periodic-scripts` are useful for running tasks that need to occur 
on a repeated basis. These scripts can be used to collect data from
external sources, run reports, or perform maintenance tasks. This document
describes how a Developer can write custom Periodic Scripts to be run by BMON.

:ref:`Reading BMON Data via an API <api-data-access>`
-----------------------------------------------------

A basic Application Programming Interface (API) is available to read data
from the BMON application.  Also, a Python library wrapping the API is available
to simplify data access.
