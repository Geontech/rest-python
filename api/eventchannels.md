---
layout: api_page
title:  Event Channels
group:  API
order:  8
---
{% include JB/setup %}
{% include rest_setup %}
{% include rest_url.md rest_path=rest_events %}

Event Channels exist outside of the Domain since they are a part of the underlying network infrastructure.  However in the context of rest-python, we maintain the _nod_ that event channel data often contains the domain of origin.  So, we maintain that in this API.

By opening a websocket connection to the above URL, one can _subscribe_ to specific event channels using the channel name, called a `topic` in websocket parlance, and the Domain ID (name) by writing the following JSON structure to the socket:

{% highlight json %}
{ 
    command  : 'ADD',
    domainId : 'DOMAIN_NAME',
    topic:     'ODM_Channel'
}
{% endhighlight %}

Conversely, _unsubscribing_ is accomplished by changing the `command` to `REMOVE`.  Also note, in this example, we've used the `ODM_Channel`.  Replace that string name with another named channel of your choice.

Once open the channel will begin pushing structures of JSON data according to what is being seen on the channel, either Events or Messages. 

### Events

These structures are exclusively defined as one would find on the ODM and IDM channels in a REDHAWK system since those structures are simply converted into dictionaries and lists, as appropriate, but using JSON for syntax.  

Enumerations are handled as they are for [properties](/api/properties.html): 

{% include property_enum.md %}

Moreover, the `sourceIOR` and other object reference types are stripped since they're of little use on the other side of the socket.  Instead you will see the key name, like `sourceIOR`, but the value will be a string indicating it does not represent what the real value was in any way.

### Messages and propEvent Ports

At present the best way to get Messages and property change events out of rest-python is to attach the associated port (in REDHAWK) to a named event channel.  Then as described above, subscribe to that channel name as your topic to read those messages and property events as they happen.

>**NOTE:** At this time we do not have a way to inject messages back into an event channel.  If you would like to write the handlers for this, please do so and submit a pull request.  Otherwise, just know it's on our _To Do_ list. :-)

The important thing to remember about these structures is they're going to mirror either your defined structure (for Messages) or the property changed event type, as defined by REDHAWK SDR.