---
title: "Inspecting a Component"
rest_url:  component
group:  component
layout: post
tags:   ["HTTP GET"]
order:  1
---
{% include JB/setup %}
{% highlight javascript %}
{
    "id":       "componentId",
    "name":     "componentName",
    "started":  false,  /* or true */
    "properties": [
        /* List of property structures */
    ],
    "ports": [
        /* List of port structures */
    ]
}
{% endhighlight %}