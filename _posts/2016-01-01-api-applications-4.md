---
title: "Inspecting an Application"
rest_url:  application
group:  waveform
layout: post
tags:   ["HTTP GET"]
order:  4
---
{% include JB/setup %}
{% highlight javascript %}
{
    "id":           "applicationId",
    "name":         "waveformName",
    "started":      true,           /* or false */
    "components": [
        {
            "name": "Component1", 
            "id": "Component1_1:waveformName_020_094846958_1"
        }, 
        {
            "name": "Component2", 
            "id": "Component2_1:waveformName_020_094846958_1"
        }
    ],
    "properties": [], /* Unused at this time */
    "ports": [
        /* List of port structures for any marked External. */
    ]
}
{% endhighlight %}

The `components` list can be indexed into using the `id` field (see [Components](/api/component.html)).