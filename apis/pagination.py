import urllib


# Function to parse pagination
def next_page(response):
    # response['links']['next']
    try:
        pagination = urllib.parse.parse_qs(response['links']['next'],
                                           keep_blank_values=False, strict_parsing=False,
                                           encoding='utf-8', errors='replace',
                                           max_num_fields=None, separator='&')
        pagination = pagination['starting_after'][0]
    except:
        pagination = None
    return pagination


