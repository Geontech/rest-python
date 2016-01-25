---
title: "List Components"
rest_url:  components
group:  component
layout: post
tags:   ["HTTP GET"]
order:  0
---
{% include JB/setup %}
{% highlight javascript %}
{
    "components": [
        { 
            "id":   "componentId", 
            "name": "componentName" 
        }
    ]
}
{% endhighlight %}

The `components` list can be indexed further by using the `id` field of interest.