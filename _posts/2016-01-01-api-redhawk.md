---
title: "Monitoring the Addition and Removal of Domains"
rest_url:  redhawk
group:  redhawk
layout: post
tags:   ["WEBSOCKET READ"]
order:  1
---
{% include JB/setup %}
{% highlight javascript %}
{
    "domains": [ /* List of Domain Names */ ],
    "added":   [ /* Those Added */ ],
    "removed": [ /* Those Removed */]
}
{% endhighlight %}

This stream continually polls at roughly once per second on the server side so that multiple clients remain synchronized without bombarding the server with HTTP GET requests.  So rather than having to poll `{{ site.rest_api['domains'] }}` to keep track of changes manually, this socket will instead push not only the list of known Domains but also `added` and `removed` lists for simple top-level management of which REDHAWK Domains are presently online.  