---
title: events
group: events
layout: post
tags: ['WEBSOCKET WRITE']
order: 0
---
By opening a websocket connection to the above URL, one can _subscribe_ to specific event channels using the channel name, called a `topic` in websocket parlance, and the Domain ID (name) by writing the following JSON structure to the socket:

{% highlight javascript %}
{ 
    'command'  : 'ADD',
    'domainId' : 'DOMAIN_NAME',
    'topic':     'ODM_Channel'
}
{% endhighlight %}

Conversely, _unsubscribing_ is accomplished by changing the `command` to `REMOVE`.  Also note, in this example, we've used the `ODM_Channel`.  Replace that string name with another named channel of your choice.

Once open the channel will begin pushing structures of JSON data according to what is being seen on the channel, either Events or Messages. 