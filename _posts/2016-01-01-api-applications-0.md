---
title: "Listing Applications"
rest_url:  applications
group:  waveform
layout: post
tags:   ["HTTP GET"]
order:  0
---
{% include JB/setup %}
{% highlight javascript %}
{
    "applications": [
        /* List of waveform IDs that are launched */
        {
            "name": "waveformName_020_094846958", 
            "id":   "DCE:d6ca6b70-033f-425b-a88a-a407efaba0ef:waveformName_020_094846958_1"
        }
    ], 
    "waveforms": [
        /* List of waveforms that are installed/available */
        {
            "name": "waveformName",
            "sad":  "/waveforms/waveformName/waveformName.sad.xml"
        }
    ]
}
{% endhighlight %}

One can index into the `applications` list using one of the provided `id`.