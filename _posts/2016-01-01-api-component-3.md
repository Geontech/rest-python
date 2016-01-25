---
title: "Setting Component Properties"
rest_url:  properties
group:  component
layout: post
tags:   ["HTTP PUT"]
order:  3
---
{% include JB/setup %}
{% highlight javascript %}
{
    "properties": [ 
        /* simplified list of properties */
        {
            "id":       "propertyId",
            "value":    ""  /* As appropriate */   
        },
    ]
}
{% endhighlight %}

The `properties` field is a list of structures which follow the structures defined in [Properties](/api/properties.html) with the exception that only the `id` and `value` fields are important.  Everything else is optional and _will be ignored at the server_.

Unlike Devices, Component properties can only be configured (the function of which only returns `void`).  Therefore the server does not emit a response structure as it does for Devices.