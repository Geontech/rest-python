---
title: "Getting Component Properties"
rest_url:  properties
group:  component
layout: post
tags:   ["HTTP GET"]
order:  2
---
{% include JB/setup %}
{% highlight javascript %}
{
    "properties": [
        /* List of property structures */
    ]
}
{% endhighlight %}

The `properties` field is a list of structures indexed by `id` following this general format:

{% include property.md %}

For more information on the structures, see [Properties](/api/properties.html).