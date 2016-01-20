---
layout: api_page
title:  Properties
group:  API
order:  7
---
{% include JB/setup %}

The rest-python server handles properties differently based on where one is at in the system.  This document mean to focus on the `CF::Properties` lists that accompany [Devices](/api/device.html) and [Components](/api/component.html).  For all others, see their documentation.

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

{% include api_post_list.html post_group='properties' %}