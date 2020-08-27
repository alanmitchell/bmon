.. _setting-up-lora-sensors-to-post-to-bmon:

Setting Up LoRa Sensors to Post to BMON
=========================================

This page gives specific instructions on how to set up LoRa
sensors to post their data to a BMON system. In
addition, general documentation has been provided on how to set up a LoRaWan
communication Gateway and creating payload applications for LoRa sensors 
in `The Things Network <https://www.thethingsnetwork.org>`_ (TTN) which integrates
with your BMON system.


#######################################################
Before you Begin - First time The Things Network Setup
#######################################################

Skip to step 6 `Register Your Device`_ if you already have a preexisting TTN account and application configured for the device type.

#. Visit `TTN <https://account.thethingsnetwork.org/register>`_ and create a free account
#. `Add your LoRa Gateway to TTN`_
#. `Create an Application in TTN`_ for each sensor type/manufacturer
#. `Add an HTTP integration for BMON`_
#. `Add a payload decoder to TTN`_ for the sensor 
#. `Register Your Device`_

.. note:: You typically only need to create *one* application per device manufacturer - many manufacturers use a unified payload format across their devices though some may write custom payload decoders by device, see your sensor documentation for more information.

**Add your LoRa Gateway to TTN**
----------------------------------

The gateway will require some general setup that is not covered in this documentation as it has been thoroughly documented by The Things Network and is also unique to your make/manufacturer's LoRa Gateway hardware.

The general setup for a gateway in the United States (west coast) will look similar to this in TTN
	.. image:: /_static/ttn_gateway.jpg



	* `Instructions for adding a Laird LoRa Gateway to TTN <https://www.thethingsnetwork.org/docs/gateways/laird/>`_
	* `Instructions for adding a The Things Indoor Gateway to TTN <https://www.thethingsnetwork.org/docs/gateways/thethingsindoor/>`_
	* `More gateways on TTN <https://www.thethingsnetwork.org/docs/gateways/>`_


**Create an Application in TTN**
--------------------------------

* Following the `TTN documentation <https://www.thethingsnetwork.org/docs/applications/add.html>`_ create an ``Application`` for each sensor/type you have
* Here is an example of a Dragino Application
	.. image:: /_static/ttn_app_overview2.jpg

.. note:: you can select ``manage euis`` from this page to add the specific EUI provided by the device manufacturer, this EUI will be the same for every sensor of this type. Adding the EUI at this level means you don't have to enter it for each device during registration, simply make sure it is selected when registering your device later.

**Add an HTTP integration for BMON**
----------------------------------------

* With the application you just made still open in TTN, click the ``Integrations`` tab
* Next, select ``add integration``
* From the list of options, select ``HTTP Integration`` 
* Here is an example Dragino integration
	.. image:: /_static/ttn_html_integration.jpg

where:
    * ``Process ID:`` by using bmon-dragino here we can easily tell from a glance that the process is used for BMON and is for the Dragino sensor. 
    * ``Access Key:`` select *default key [devices] [messages]*
    * ``URL:`` You should use your BMON url/readingdb/reading/store-things/ ex. http://bms.ahfc.us/readingdb/reading/store-things/
    * ``Method:`` select POST as this is a data posting event
    * ``Authorization:`` leave blank
    * ``Custom Header Name:`` use *store-key* here
    * ``Custom Header Value:`` Your *BMSAPP_STORE_KEY* from ``settings.py``


**Add a payload decoder to TTN**
------------------------------------

* Locate the payload decoder for your device, or write your own depending on your needs
* With the correct sensor application open in TTN, click the ``Payload Formats`` tab
* Select ``Custom`` for ``Payload Format``
* Make sure the ``decoder`` tab is selected and paste the contents of your payload decoder into the code field
* Scroll down and click ``save``

	.. image:: /_static/ttn_dragino_payload.jpg


**Payload Decoders**

* `Dragino Downloads <http://www.dragino.com/downloads/downloads/>`_
* `Dragino LHT65 official payload decoder <http://www.dragino.com/downloads/downloads/LHT65/payload_decode/ttn_payload_decode.txt>`_
* :download:`Dragino decoder </_static/dragino_payload.txt>` (locally hosted)
* `Elsys official payload decoder (scroll to TheThingsNetwork decoder) <https://www.elsys.se/en/elsys-payload/>`_
* :download:`Elsys decoder </_static/elsys_payload.txt>` (locally hosted)
* :download:`Netvox Lux decoder </_static/netvox_lux_payload.txt>` (locally hosted)



**Register Your Device**
-------------------------

* Navigate back to the relevant application for your device (ex. Dragino)
* With the application open, click the ``Integrations`` tab
* Next, select ``register device``
* Using information provided by the sensor manufacturer, complete the device registration form 
	.. image:: /_static/ttn_register_device.jpg

        * For ``Device ID`` you can make up an ID tough it helps to quickly identify the device later on by using a naming convention like: lht65-a84041000181c74e, with LHT65 as the Dragino sensor model, and the long string is the Device EUI.
        * ``Device EUI`` is generally printed on the sensor.
        * ``App Key`` is the secret key that also comes with the sensor (typically on a separate document)
        * ``App EUI`` should be the same for **every** sensor of this type.  It should also be included with the sensor.  You can enter it at the Application level, and it will show up here as a default.
			* TTN likes to to generate it's own EUI here if you haven't already entered one, overwrite this function by clicking the edit "pencil" icon


#################################
Adding Your LoRa Device to BMON
#################################

The beauty of this system is that as soon as the HTTP integration is made for BMON and the sensors start reporting to the gateway connected to TTN you'll start seeing your sensors in BMON almost immediately. 

Here is an example Dragnio LHT65 sensor taken from the `unassigned-sensors` page of a BMON site once the TTN HTTP integration started communicating with BMON. 
	.. image:: /_static/bmon_lora_ex.jpg
	
	* ``A84041##########_BatV`` - common on most LoRa sensors, BatV indicates the sensor's battery in Voltage
	* ``A84041##########_rssi`` - common on most LoRa sensors, rssi indicates the sensor's received signal strength indicator. The higher the RSSI value, the stronger the signal. When measured in negative numbers, the number that is closer to zero usually means better signal.
	* ``A84041##########_snr`` - common on most LoRa sensors, snr indicates the signal-to-noise ratio
	* ``A84041##########_Hum_SHT`` - Dragino Humidity 
	* ``A84041##########_TempC_DS`` - Dragino external probe Temperature (C) 
	* ``A84041##########_TempC_SHT`` - Dragnio internal Temperature (C)
	
`Follow these instructions to add your sensor to the BMON system <adding-buildings-and-sensors.html#adding-sensors>`_.

########################
Resources
########################

*  `Laird Sentrius RG1xx LoRaWAN Gateway <https://www.lairdconnect.com/wireless-modules/lorawan-solutions/sentrius-rg1xx-lorawan-gateway-wi-fi-ethernet-optional-lte-us-only/>`_
*  `Dragino LHT65 Temperature and Humidity sensor <http://www.dragino.com/products/lora-lorawan-end-node/item/151-lht65.html>`_ 
*  `Elsys ERS CO2/Lux/PIR/Temperature/Humidity Sensor <https://www.elsys.se/shop/product/ers-co2/?v=7516fd43adaa>`_
*  `Netvox R311G Lux Sensor <http://www.netvox.com.tw/product.asp?pro=R311G>`_
*   For further information and discussion on LoRa equipment visit the `BMON forum <https://forum.bmon.org/c/hardware/lora/11>`_


