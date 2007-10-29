import re
from cgi import escape

from django.utils.text import truncate_words, normalize_newlines
from django.utils.html import strip_tags, clean_html
       
from utils.html import decode_entities
        
def format_subject(text, from_body=False):
    """    
    Remove HTML tags
    Replace entities with unicode value
    Schrink to 80 chars max
    Strip starting and trailing white space
    TODO : remove new lines
    """
    if from_body:
        return decode_entities(strip_tags(text.replace()))[:80].strip()
    else:
        return escape(text)[:80].strip()
        
#def format_subject_from_body(text):
#    """
#    This function is only called with data parsed from format_body
#    Remove HTML tags
#    Replace entities with unicode value
#    Schrink to 80 chars max
#    Strip starting and trailing white space
#    TODO : remove new lines
#    """
#    return 'dont use it!'
    


def format_body(html):
    """
    Convert all new lines to \n
    Convert HTML entities to unicode
    # TODO : new html_filter to strip javascript
    Clean HTML
    Strip starting and trailing white space
    """
    return clean_html( decode_entities( normalize_newlines(html) ) ).strip()