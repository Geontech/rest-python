---
layout: api_page
title:  REDHAWK
group:  API
order:  0
---
{% include JB/setup %}
{% include rest_setup %}
{% include rest_url.md rest_path=rest_base %}

At the very top level, the REDHAWK system, comprised of potentially multiple domains on the same OmniORB service, is accessed at the above address.

No REST actions exist at this URL.  Instead, this is how one accesses two different sockets of data: REDHAWK events, and Event Channels for specific domains.

### REDHAWK Events

{% include rest_url.md rest_path=rest_redhawk %}

Opening a websocket to this URL yields JSON data for which Domains are active.  So rather than having to poll `{{ rest_domains }}` to keep track of changes manually, this socket will instead push not only the list of known Domains but also `added` and `removed` lists for simple top-level management of which REDHAWK Domains are presently online.  The structure is as follows:

{% highlight json %}
{
    domains: [ List of Domain Names ],
    added:   [ Those Added ],
    removed: [ Those Removed ]
}
{% endhighlight %}

This stream continually polls at roughly once per second on the server side so that multiple clients remain synchronized without bombarding the server with HTTP GET requests.

### Event Channels

{% include rest_url.md rest_path=rest_events %}

Event channels are a very complex and flexible topic best reserved for its own page, found [here](/api/eventchannels.html).  The fundamental gist is the context of event channels is generally derived by the Domain or origin.  But what can be sent on Event Channels can be a number of different things, hence why it deserves its own section.
