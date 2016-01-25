---
title: "Launching a Waveform"
rest_url:  applications
group:  waveform
layout: post
tags:   ["HTTP POST"]
order:  1
---
{% include JB/setup %}
{% highlight javascript %}
{
    "name":     "waveformName",
    "started":  true            /* OPTIONAL */
}
{% endhighlight %}

Posting this structure, the Waveform named `name` will result in an attempt to launch a Waveform.  If `started` is provided and `true`, the server will attempt to start the Waveform as well.

The server will respond with:

{% include app_launch_response.md %}