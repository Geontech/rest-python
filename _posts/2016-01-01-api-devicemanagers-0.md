---
title: "Listing Device Managers"
rest_url:  devicemanagers
group:  devicemanager
layout: post
tags:   ["HTTP GET"]
order:  0
---
{% include JB/setup %}
{% highlight javascript %}
{
    "deviceManagers": [
        {   
            "name": "nodeName", 
            "id":   "nodeID"
        }
    ], 
}
{% endhighlight %}

This `deviceManagers` URL can be indexed using the `id` field of interest.