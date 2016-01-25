---
title: "Inspecting a Device Manager"
rest_url:  devicemanager
group:  devicemanager
layout: post
tags:   ["HTTP GET"]
order:  1
---
{% include JB/setup %}
{% highlight javascript %}
{
    "name":     "TestNode", 
    "id":       "DCE:d0645c12-7962-414f-9969-2372635b1170"
    "properties": [ 
        {
            "scaType":  "simple", 
            "id":       "HOSTNAME", 
            "value":    "localhost.localdomain"
        }, 
        {
            "scaType":  "simple", 
            "id":       "LOGGING_CONFIG_URI", 
            "value":    ""
        }
    ], 
    "devices": [ 
        /* List of name-id objects of Devices */
        { 
            "id":   "deviceId", 
            "name": "deviceName" 
        }
    ],
    "services": [ 
        /* List of name-id objects for services */
        { 
            "id": "serviceId", 
            "name": "serviceName" 
        }
    ]
}
{% endhighlight %}

The `devices` list can be indexed further by using the `id` field of interest (see [Devices](/api/device.html)).

At this time, `services` are supported in name-only since it's not possible to represent such a nebulous entity in a useful way through this interface.