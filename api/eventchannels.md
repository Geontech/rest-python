---
layout: api_page
title:  Event Channels
group:  API
order:  8
---
{% include JB/setup %}
Event Channels exist outside of the Domain since they are a part of the underlying network infrastructure.  However in the context of rest-python, we maintain the _nod_ that event channel data often contains the domain of origin.  So, we maintain that in this API.

{% include api_post_list.html post_group='events' %}