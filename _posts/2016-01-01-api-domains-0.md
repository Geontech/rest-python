---
title: "Getting a list of Domains"
rest_url:  domains
group:  domain
layout: post
tags:   ["HTTP GET"]
order:  0
---
{% include JB/setup %}
{% highlight javascript %}
{
    "domains": [ /* List of Domain Names */ ],
}
{% endhighlight %}

Active domains are listed by their unique names in the `domains` field, the values of which can be used to further index URL.

> **NOTE:** Rather than poll this property, consider using the [REDHAWK Websocket](/api/redhawk.html).