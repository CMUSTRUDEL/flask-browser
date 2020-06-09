from functools import reduce
from app import app

def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) 
            if isinstance(d, dict) 
            else default, 
        keys.split("."), dictionary)


def is_toxic(te):
    if not te: 
        return False
    if not "toxicity" in te:
        return False
    return te['toxicity'].get(app.config['VERSION'])['score'] == 1



# def label_buttons(link, tw_id):
#     # current_label = deep_get(titem,"toxicity.manual.reason")
#     # current_label = 
#     result = []
#     for l in labels:
#         # flash({'url':link + tw_id + "/" + l[1],
#         #             'name':l[0]})
#         result += {'url':link + tw_id + "/" + l[1],
#                     'name':l[0]}
#     return result

# def render_label_buttons(label_buttons):
#     result = ""
#     for idx, b in enumerate(label_buttons):
#         result += "<a href=\""+b[0]+"\">"+b[1]+"</a>"
#         if idx < len(label_buttons)-1:
#             result += "<br>"
#         # result += "<a href=\""+b[0]+"\" class=\"labelbtn labelbtn_"+str(b[2])+"\">"+b[1]+"</a> "
#     return result

# def get_next_url(endpoint, pagination):
#     return url_for(endpoint, page=pagination.next_num) \
#         if pagination.has_next else None

# def get_prev_url(endpoint, pagination):
#     return url_for(endpoint, page=pagination.prev_num) \
#         if pagination.has_prev else None

