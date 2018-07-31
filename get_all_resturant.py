#! /usr/bin/python
# -*- coding: utf-8 -*-
'''
A script for get all restaurants from google map api

author lipuyeh
'''

import googlemaps

import time

language = 'zh-TW'

import pprint
import mongo_tools

import datetime
import pymongo

from google_map.show_all_restuarant import show_all_restaurants_details


def get_place_detail(gmaps, place_id):

    db_name = 'restaurant'
    col_name = 'raw'

    mongo_client = mongo_tools.get_mongo()
    (mongo_client[db_name][col_name].create_index("id", unique=True))
    (mongo_client[db_name][col_name].create_index("place_id", unique=True))

    results = mongo_tools.find(db_name, col_name, {'place_id': place_id})
    #print(len(results))
    if len(results) == 0:
        success = False
        detail = None
        while not success:
            try:
                #print(place_id)
                detail = gmaps.place(place_id,
                                     language=language)
                #pprint.pprint(detail)
                time.sleep(2)
                success = True
            except:
                print('get detail failed!!')
                pass
        if detail is None:
            raise Exception("datail is None!!")

        detail['result']['mtime'] = datetime.datetime.now()
        mongo_tools.insert(db_name, col_name, detail['result'])
    else:
        detail = results[0]

    return detail


def handle_near_by_results(api_results, near_by_data, handle_types=[]):

    for a_result in api_results['results']:
        output = ''
        if 'all' not in handle_types and len(set(a_result['types']) - set(handle_types)) == len(a_result['types']):
            #print(set(a_result['types']), set(handle_types), set(a_result['types']) - set(handle_types))
            continue
        else:
            pass

        place_id = a_result['place_id']
        if place_id in near_by_data:
            pass
        else:
            near_by_data[place_id] = a_result

        if 'name' in a_result:
            output += a_result['name'] + ' '
        if 'rating' in a_result:
            output += str(a_result['rating']) + '\n'
        if 'types' in a_result:
            output += ' '.join(a_result['types']) + '\n'
        if 'vicinity' in a_result:
            output += a_result['vicinity']

        output += '\n'
        #print(output)

    return near_by_data


def get_all_restaurants_details(gmaps, restaurant_data):

    output = []
    for a_id in restaurant_data:
        detail = get_place_detail(gmaps, a_id)
        #pprint.pprint(detail)
        output.append(detail)

    return output


def get_data_from_address_and_gmap(gmaps, address, search_types, radius=300, rank_by=None):

    gmaps = googlemaps.Client(key=key)
    restaurant_data = {}
    all_data = {}
    g_location = gmaps.geocode(address, language=language)
    #print(g_location)
    if len(g_location) > 1:
        print('more than 1 location!!')
        pprint.pprint(g_location)
    location = (g_location[0]['geometry']['location']['lat'], g_location[0]['geometry']['location']['lng'])

    available_search_types = ['restaurant', 'all']
    x = gmaps.places_nearby(location=location,
                            language=language, rank_by=rank_by,
                            type=search_types, radius=radius)

    all_map_data = {}

    all_data = handle_near_by_results(x, all_data, ['all'])
    all_map_data['all'] = all_data

    if 'restaurant' in search_types:
        restaurant_data = handle_near_by_results(x, restaurant_data, ['restaurant'])
        all_map_data['restaurant'] = restaurant_data

    #add check for not use type in search_types
    if len(set(search_types) - set(available_search_types)) != 0:
        raise Exception("un availabel types!! %s" % (search_types))

    #print(x)
    if 'next_page_token' in x:
        page_token = x['next_page_token']
    else:
        page_token = None

    while page_token is not None:
        #print(page_token)
        time.sleep(2)

        data = gmaps.places_nearby(page_token=page_token)
        handle_near_by_results(data, restaurant_data, search_types)
        if 'next_page_token' in data:
            page_token = data['next_page_token']
        else:
            page_token = None

    return all_map_data


def get_restaurants_from_address(gmaps, address, search_types, radius=300, rank_by=None):
    """
    need to update if want to use on multiple types, now only for restaurant!!
    like cond need to add search_types for index
    """
    db_name = 'restaurant'
    col_name = 'address_data'

    # first load from mongo, if not exist, get from google api
    cond = {"address": address,
            "radius": radius,
            "rank_by": rank_by}
    #print(cond)
    mongo_client = mongo_tools.get_mongo()
    mongo_client[db_name][col_name].create_index([("address", pymongo.ASCENDING), ("radius", pymongo.ASCENDING),
                                                 ("rank_by", pymongo.ASCENDING)], unique=True)

    results = mongo_tools.find(db_name, col_name, cond)
    #print(len(results))

    if len(results) == 0:
        all_map_data = get_data_from_address_and_gmap(gmaps, address, search_types, radius=radius, rank_by=rank_by)
        restaurant_data = all_map_data['restaurant']
        all_data = {'restaurant_data': restaurant_data,
                    'mtime': datetime.datetime.now(),
                    'search_types': search_types,
                    'radius': radius,
                    'address': address,
                    'rank_by': rank_by}
        mongo_tools.insert(db_name, col_name, all_data)
        all_data = all_map_data['all']

        # now all data is only save for future possible!!
        db_name = 'all'
        col_name = 'address_data'
        all_data = {'data': all_map_data['all'],
                    'mtime': datetime.datetime.now(),
                    'search_types': search_types,
                    'radius': radius,
                    'address': address,
                    'rank_by': rank_by}
        mongo_tools.insert(db_name, col_name, all_data)

    else:
        try:
            restaurant_data = results[0]['restaurant_data']
        except:
            pprint.pprint(results)
            xxx

    return restaurant_data


def get_address_from_restaurant_details(restaurant_details):

    all_address = []
    for a_detail in restaurant_details:
        #pprint.pprint(a_detail)
        if 'formatted_address' in a_detail:
            all_address.append(a_detail['formatted_address'])
        else:
            pass

    return all_address

if __name__ == '__main__':

    # key is the string of google api key
    import key_tools
    key = key_tools.get_google_key()[0]

    gmaps = googlemaps.Client(key=key)

    #address = '台北市牯嶺街22巷8號'
    #address = '台北市中山區南京西路12號'
    #address = '台北市牯嶺街1號'
    address = '台北市臨沂街44巷'
    #address = '台北市臨沂街57巷2號'
    #address = '中山區南京西路25巷4-3號'  # 259
    #address = '台北市大安區信義路二段194號'  # 288
    #address = '台北市大安區永康街41巷12號'  # 301
    #address = '台北市中正區金山南路一段120號'  # 314
    #address = '台北市大安區麗水街3之1號'  # 383
    #address = '台北市大安區建國南路一段198'  # 521
    #address = '台北市中正區忠孝東路一段178號'  # 618, exceed daily api

    radius = None
    rank_by = 'distance'
    radius = 500
    radius = 100
    rank_by = None

    search_types = ['restaurant']

    restaurant_data = get_restaurants_from_address(gmaps, address, search_types, radius=radius, rank_by=rank_by)
    restaurant_details = get_all_restaurants_details(gmaps, restaurant_data)
    #show_all_restaurants_details(restaurant_data)

    all_address_1 = get_address_from_restaurant_details(restaurant_details)

    for a_address in all_address_1:
        restaurant_data = get_restaurants_from_address(gmaps, a_address, search_types, radius=radius, rank_by=rank_by)
        restaurant_details = get_all_restaurants_details(gmaps, restaurant_data)
        all_address_2 = get_address_from_restaurant_details(restaurant_details)
        for b_address in all_address_2:
            restaurant_data = get_restaurants_from_address(gmaps, b_address, search_types, radius=radius, rank_by=rank_by)
            restaurant_details = get_all_restaurants_details(gmaps, restaurant_data)
            all_address_3 = get_address_from_restaurant_details(restaurant_details)
            for c_address in all_address_3:
                restaurant_data = get_restaurants_from_address(gmaps, c_address, search_types, radius=radius, rank_by=rank_by)
                restaurant_details = get_all_restaurants_details(gmaps, restaurant_data)
                all_address_4 = get_address_from_restaurant_details(restaurant_details)
                print('a_c')
            print('a_b')
        print('a_a')
