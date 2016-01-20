---
title: "Inspecting a Domain"
rest_url:  domain
group:  domain
layout: post
tags:   ["HTTP GET"]
order:  1
---
{% include JB/setup %}
{% highlight javascript %}
{
    "name": "REDHAWK_DEV", 
    "id": "DCE:9ae444e0-0bfd-4e3d-b16c-1cffb3dc0f46", 
    "properties": [
        {
            "scaType": "simple", 
            "id": "COMPONENT_BINDING_TIMEOUT",
            "value": 60
        }, 
        {
            "scaType": "simple", 
            "id": "LOGGING_CONFIG_URI", 
            "value": ""
        }, 
        {
            "scaType": "simple", 
            "id": "REDHAWK_VERSION", 
            "value": "1.10.1"
        } 
    ], 
    "applications": [
        { 
            "name": "applicationName",
            "id":   "applicationId"
        }
    ], 
    "deviceManagers": [
        {   
            "name": "nodeName", 
            "id": "nodeId"
        }
    ], 
    "eventChannels": [
        /* List of event channel names as strings */
    ]
}
{% endhighlight %}

The `applications` field lists all running [Waveforms](/api/waveform.html).  Likewise `deviceManagers` lists the known [Device Managers](/api/devicemanager.html) in the system.  Both of these lists can be indexed further using the `id` field of interest.

The `eventChannels` field provides a list of any event channels to which one has subscribed using the `{{site.rest_api['events']}}` websocket interface ([Event Channels](/api/eventchannels.html)).  This list **cannot** be indexed.