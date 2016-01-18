---
title: events
group: events
layout: post
tags: ['WEBSOCKET READ']
order: 2
---
#### Messages and propEvent

Messages and propEvent ports convey their information as property ID-value streams:

{% highlight javascript %}
{
    'id':     'propertyId',
    'value':  [ /* List of id-value pairs */ ]
}
{% endhighlight %}

No propety type information is included in this structure at this time.  The important thing to remember about these structures is they're going to mirror either your defined structure (for Messages) or the property changed event type, as defined by REDHAWK SDR.

At present the best way to get Messages and property change events out of rest-python is to attach the associated port (in REDHAWK) to a named event channel.  Then subscribe to that channel name as your topic to read those messages and property events as they happen.

**NOTE:** At this time we do not have a way to inject messages back into an event channel.  If you would like to write the handlers for this, please do so and submit a pull request.  Otherwise, just know it's on our _To Do_ list. :-)
