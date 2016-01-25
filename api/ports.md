---
layout:     api_page
title:      Ports
group:      API
subgroup:   ports
order:      6
---
{% include JB/setup %}
The handling of ports in rest-python takes on several forms depending on the IDL defining the port.  Devices, Components, and Waveforms provide a `ports` list.  The URL to each of those entities should be substituted for the `PARENT_PATH` listed in this document.

> **NOTE:** Not all port types support providing extra information.  The ones that do are detailed here.  

{% include api_post_list.html %}