#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
show restuarant in db

author lipuyeh
"""

import mongo_tools
import pprint


def show_a_restuarant(a_restuarant_data):

    output = "\n"
    output_key = ['name', 'formatted_address', 'formatted_phone_number', 'rating']
    for a_key in output_key:
        if a_key not in a_restuarant_data:
            output = '%s: no data\n' % (a_key)
        else:
            output += '%s: %s\n' % (a_key, a_restuarant_data[a_key])

    if 'reviews' in a_restuarant_data:
        for a_review in a_restuarant_data['reviews']:
            output += '%s(%d, %s): %s\n' % (a_review['author_name'],
                                            a_review['rating'],
                                            a_review['relative_time_description'],
                                            a_review['text'].replace("\n", ""),)
    else:
        output += 'reviews: no data\n'

    for a_key in ['url', 'website']:
        if a_key not in a_restuarant_data:
            output = '%s: no data\n' % (a_key)
        else:
            output += '<a href="%s">%s</a>\n' % (a_restuarant_data[a_key], a_key)

    #pprint.pprint(a_restuarant_data)
    print(output.replace("\n", "<br>\n"))


def show_all_restaurants_details(restaurant_data):

    db_name = 'restaurant'
    col_name = 'raw'

    for a_id in restaurant_data:
        cond = {'place_id': a_id}
        results = mongo_tools.find(db_name, col_name, cond)
        show_a_restuarant(results[0])


def show_all_restaurants_details_from_db(location=None):

    if location is None:
        cond = {}
    else:
        raise Exception('Not implemented function!!')

    db_name = 'restaurant'
    col_name = 'raw'

    mongo_client = mongo_tools.get_mongo()
    cursor = mongo_client[db_name][col_name].find(cond)

    count = 0
    for a_detail in cursor:
        count += 1
        show_a_restuarant(a_detail)

    print('%d restuarants!!' % count)

if __name__ == '__main__':

    show_all_restaurants_details_from_db()

    pass
