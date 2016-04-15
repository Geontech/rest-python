---
layout: page
title: Welcome!
---
{% include JB/setup %}

Welcome to the documentation for [Geon Technology's](http://www.geontech.com) fork of [rest-python](http://github.com/geontech/rest-python).  

Our goal for extending the [REDHAWK SDR](http://github.com/redhawksdr/rest-python) version was to stabilize and add as many features as possible to better support a generic interface to a [REDHAWK SDR](http://www.redhawksdr.org) system using open and modern web technologies of the end-user's choosing.  These features include both observing and controlling the systems within the Domain.  In essence: the aim is for an easy-to-use backend for interfacing with other systems or developing light-weight user interfaces.

>**NOTE:** This version of rest-python has been tested against REDHAWK 1.9.0 through 2.0.0.  In an upcoming release, previous versions will no longer be updated as features exclusive to REDHAWK 2.0 will soon be added.

## Installation

The rest-python interface is a Tornado webserver that relies on the Python interface to the REDHAWK SDR system (a.k.a., the sandbox in `ossie.utils`, among others).  Therefore it must be running on a system that has access to those libraries, but not necessarily the system running the Domain.  Beyond that requirement, installation on your Linux distribution will vary.  

See the [README.md](https://github.com/Geontech/rest-python/blob/master/README.md) for more detailed installation and startup instructions.

## Deploying Applications

The server is configured to index any directory structure in the `/apps/` or `/client/` paths.  The resulting URL would then be `http://localhost:8080/apps/MySpecialApp`, assuming there is an `index.html` in that directory.  

If you are developing a new application or interface and would like to  the server in `--debug` mode allows the server to re-index those paths as files change (to support development.)
