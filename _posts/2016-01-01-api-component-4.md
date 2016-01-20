---
title: "Listing Component Ports"
rest_url:  ports
group:  component
layout: post
tags:   ["HTTP GET"]
order:  4
---
{% include JB/setup %}
{% highlight javascript %}
{
    "ports": [
        /* List of port structures */
    ]
}
{% endhighlight %}

The general format for ports is shown here:

{% include port.md %}

The list can be indexed using the `name` field.  See [Ports](/api/ports.html) for more information.