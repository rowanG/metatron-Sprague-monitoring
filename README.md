Scaramanga
==========

Please note: This is a fork from the Metatron Sprague Monitoring project.
Whilst I was lead developer on that project, this fork ensures the latest
stable and unstable versions.

What is Scaramanga
------------------
Scaramanga is a monitoring tool designed for large (46 inch) TV screens.
The aim is to make this more dynamic so it fits screen sizes of all shapes.
It currently all resides within a single Python file, this will be changed
and made modular at a later date.
It allows for data to be displayed in a fun, creative, yet useful way.
The layout is similar to that of Windows 8.

How does it work, and what technologies power it? (Javascipt? Php? C#?)
-----------------------------------------------------------------------
Absolutely and categorically no to each of those languages.
Scaramanga is powered by Python on the Web, thanks to the Flask framework.
This makes it versatile, interactive, flexible and not dependant on 
one system to host.
Currently it is connected to a Microsoft SQL database which could not be
replaced, but if another database such as MySQL or SQLite is to be used
it can be easily changed.
And due to the nature of Python, it's syntaxically beautiful.

Requirements
------------
The following packages have to be installed on the host system:

* Easysoft ODBC Driver (or OpenSource alternative)
* Python2.7+ (Python 3.x not supported)
* Python Flask
* PyODBC
* _mssql


