---
layout:     api_page
title:      Properties
group:      API
subgroup:   properties
order:      7
---
{% include JB/setup %}

The rest-python server handles properties differently based on where one is at in the system.  This document mean to focus on the `CF::PropertySet` lists that accompany [Devices](/api/device.html) and [Components](/api/component.html).  For all others, see the associated documentation.  Care was taken to keep the structures similar even if not all fields could be inferred.

### General structure

{% include property.md %}

### Representations of "value"

**SIMPLE**
{% include property_simple_value.md %}

**SIMPLESEQ**
{% include property_simpleseq_value.md %}

**STRUCT**
{% include property_struct_value.md %}

**STRUCTSEQ**
{% include property_structseq_value.md %}

### Example

The following is an example of a `configure` `event` `struct` property where one of the fields is an enumeration and the other is a string.  The field IDs are: `struct_event_prop::field1` and `struct_event_prop::field2`.

{% highlight javascript %}
{
    "id": "struct_event_prop"
    "name": "struct_event_prop", 
    "mode": "readwrite", 
    "scaType": "struct", 
    "kinds": ["configure", "event"], 
    "value": [
        {
            "enumerations": {"SOMETHING_ELSE": 1, "SOMETHING": 0}, 
            "kinds": ["configure", "event"], 
            "name": "field2", 
            "value": 0, 
            "scaType": "simple", 
            "mode": "readwrite", 
            "type": "ulong", 
            "id": "struct_event_prop::field2"
        }, 
        {
            "kinds": ["configure", "event"], 
            "name": "field1",
            "value": "test_value", 
            "scaType": "simple", 
            "mode": "readwrite", 
            "type": "string", 
            "id": "struct_event_prop::field1"
        }
    ], 
}, 
{% endhighlight %}

{% include api_post_list.html %}