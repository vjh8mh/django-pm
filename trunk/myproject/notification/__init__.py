 # -*- coding: utf-8 -*-

def notification(request, message, **kwargs):
    """
    User notification system through request.session
    
    Basic usage:
    ------------
    >>> from notification import notification
    >>> notification(request, 'Hey, user, here is your feeback!')
    
    
    Twisted usage:
    --------------
    Define your notice template in the ``notification.context_processors.NOTICE_LAYOUTS`` dict:
    {
    'notice_link': '<li class="%(css_class)s">%(message)s <a href="%(link_url)s">%(link_text)s</a></li>',
    }
    
    >>> notification(request,
               'Hey, feedback again, check out the link !',
               layout = 'notice_link',
               link_url = 'http://yahoo.com/',
               link_text = 'Yahoo!'
               )
               
    The notification.context_processors.notices check for new notice messages
    in the ``notices`` list ( each notice is a dict with your keywords )
    The context_processor adds a ``as_html`` key with the html taken from 
    the NOTICE_TEMPLATES['template']
    
    It looks like this in the templates :
    
    {% block notification %}
    {% if notices %}
    <div id="notice" class="yui-g">
    <ul>
    {% for notice in notices %}{{ notice.as_html }}{% endfor %}
    </ul>
    </div>
    {% endif %}
    {% endblock notification %}
    
    If you wish to display notifications elsewhere on a special page, just do:
    {% block notification %}{% endblock notification %}
    And define the layout elsewhere.
    
    Or customise on the template with whatever you passed:
    >>> notification(request, 'Custom message!', custom_key="weird_class")
    
    {% if notices %}
      {% for notice in notices %}
        {% if notice.custom_key %}<span class="{{ notice.custom_key }}">{{ notice.message }}</span>
        {% else %}{{ notice.as_html }}{% endif %}
      {% endfor %}
    {% endif %}
    
    """
    
    # get pending messages
    msgs = request.session.get('notice', {})
    
    # add the message at the end of the message queue
    kwargs['message'] = message
    msgs.update({len(msgs): kwargs})
    
    request.session['notices'] = msgs
    
