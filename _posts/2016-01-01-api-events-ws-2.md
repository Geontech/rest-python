---
title: events
group: events
layout: post
tags: ['WEBSOCKET READ']
order: 1
---
#### ODM and IDM Events

These structures are exclusively defined as one would find on the ODM and IDM channels in a REDHAWK system since those structures are simply converted into dictionaries and lists, as appropriate, but using JSON for syntax.  For example:

{% highlight javascript %}
{
    'sourceId':         'DCE:820e3275-4462-4823-b754-e09b4712869e', 
    'sourceName':       'FEI_FileReader_1', 
    'sourceCategory':   'DEVICE', 
    'producerId':       'DCE:9ae444e0-0bfd-4e3d-b16c-1cffb3dc0f46'
}
{% endhighlight %}

Enumerations are handled as they are for [properties](/api/properties.html): 

{% include property_enum.md %}

Moreover, the `sourceIOR` and other object reference types are stripped since they're of little use on the other side of the socket.  Instead you will see the key name, like `sourceIOR`, but the value will be a string indicating it does not represent what the real value was in any way.