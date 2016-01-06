---
layout: page
title: Welcome!
---
{% include rest_setup %}
{% include JB/setup %}

Welcome to the documentation for [Geon Technology's](http://www.geontech.com) fork of [rest-python](http://github.com/geontech/rest-python).  

Our goal for extending the [REDHAWK SDR](http://github.com/redhawksdr/rest-python) version was to stabilize and add as many features as possible to better support a generic interface to a [REDHAWK SDR](http://www.redhawksdr.org) system using open and modern web technologies of the end-user's choosing.  These features include both observing and controlling the systems within the Domain.  In essence: the aim is for an easy-to-use backend for interfacing with other systems or developing light-weight user interfaces.

For the latter, naturally, we're a bit biased to [our own implementation](http://github.com/geontech/angular-redhawk).

## Installation

The rest-python interface is a Tornado webserver that relies on the Python interface to the REDHAWK SDR system (a.k.a., the sandbox in `ossie.utils`, among others).  Therefore it must be running on a system that has access to those libraries, but not necessarily the system running the Domain.  Beyond that requirement, installation on your Linux distribution will vary.  See the [README.md](https://github.com/Geontech/rest-python/blob/angular-redhawk/README.md) for installation instructions.

## Getting Started

>**NOTE:** At this time, the most recent version of REDHAWK that has been tested with rest-python is 1.10.2.

Along the right side of the page, you'll find a list of pages representing each piece of a REDHAWK system that is represented in this API.  The API leverages a RESTful interface, utilizing HTTP _GET_, _PUSH_, _PUT_, and _WRITE_ for most static actions.  All of these actions involve JSON structures which will be provided in more detail on each page.

To confirm rest-python is running, open a browser to its address on port 8080.  The REST interface begins at the URL `{{ rest_base }}`.  And like typical REST interfaces, the URL builds outwards using one of the returned structure's values.  

For example, navigating to the list of domains `{{ rest_domains }}` yields a single structure with an array list of names:

{% highlight json %}
{ 
    domains: [ REDHAWK_DEV, REDHAWK_DEV2 ] 
}
{% endhighlight %}

Navigating further to one of the options would be `{{ rest_domains }}/REDHAWK_DEV/`.  

That's the absolute basics of things; the individual API pages dig much deeper.