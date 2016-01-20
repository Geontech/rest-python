{% assign url_elements = site.rest_api[include.url] | split:"/" %}
{% assign result="" %}
{% for el in url_elements %}
{% if forloop.first == false %}
  {% if el contains ':' %}
    {% capture result %}{{ result }}&#47; **{{ el | remove:':' }}** {% endcapture %}
  {% else %}
    {% capture result %}{{ result }}&#47; {{ el }} {% endcapture %}
  {% endif %}
{% endif %}
{% endfor %}
{% assign url_elements = nil %}
{{ result | markdownfiy }}
{% assign result=nil %}