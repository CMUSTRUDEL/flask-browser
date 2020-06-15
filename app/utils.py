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


def get_page_details():
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE_PARAMETER']
    offset = (page - 1) * per_page
    return (page, per_page, offset)


def get_pagination(page, per_page, per_page_parameter, offset, total):
    return Pagination(page=page, 
                    per_page=per_page,
                    per_page_parameter=per_page_parameter, 
                    offset=offset,
                    prev_label="Previous",
                    next_label="Next",
                    total=total, 
                    css_framework='bootstrap3', 
                    search=False)


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

