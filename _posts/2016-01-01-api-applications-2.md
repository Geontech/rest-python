---
title: "Starting or Stopping a Waveform"
rest_url:  application
group:  waveform
layout: post
tags:   ["HTTP POST", "HTTP PUT"]
order:  2
---
{% include JB/setup %}
{% highlight javascript %}
{
    "started":  true
}
{% endhighlight %}

Either `POST` or `PUT` this structure; the Waveform at the URL will attempt to start or stop (if `started` is `false`).

The server will respond with:

{% include app_start_response.md %}