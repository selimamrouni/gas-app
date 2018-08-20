import pandas as pd
import numpy as np

from zipfile import ZipFile
import urllib.request
import xml.etree.cElementTree as et
from zipfile import ZipFile
from tqdm import tqdm
#haversine distance
from haversine import haversine
import requests

import googlemaps



def get_current_coordinate(current_address, key, country):
    """
    this function takes as input:
    - address: string
    - country: string 
    
    
    if country from google api request matches the country, then it returns the coordinates of the address: tuple 
    """
    
    gmaps = googlemaps.Client(key=key)

    # Geocoding an address
    geocode_result = gmaps.geocode(current_address)

    for i in range(len(geocode_result)):

        country_r = geocode_result[i]['address_components'][5]['long_name']

        if country_r == country:
            #if the country matches the country returned by google
            lat = geocode_result[i]['geometry']['location']['lat']
            lng = geocode_result[i]['geometry']['location']['lng']

            break 
            
    return (lat, lng)


def get_haversine(point1, point2):
    """
    The function takes as input the gps data of 2 points, and the radius of the earth.
    Based on the Haversine formula, it returns the distance (beeline) between the 2 points. 
    The distance is returned in kilometers. 
    """
    return haversine(point1, point2)


def get_gas_price(gas_type, data_gas):
    """
    takes as input:
    - a dictionnary of gas price 
    - gas type
    
    return the price of the gas type 
    """
    try:
        return float(data_gas[gas_type])
    except:
        #if can't find this gas in the station, then the station doesn't have this gas
        return 'no {} in this station ! '.format(gas_type)
    
    
def transform_coordinate(origin, destination):
    """
    function to convert 2 tuples of coordinates into a string readable by google API
    """
    ori = ','.join(str(origin)[1:-1].split(', '))
    des = ','.join(str(destination)[1:-1].split(', '))
    
    return ori,des


def get_distance_and_time(origin, destination, key):
    """
    This function takes as input:
    - origin coordinates tuple
    - destination coordinates tuple
    - API key 
    
    return:
    - tuple of real distance(in km) and time(in minute) spent by the driver
    """
    
    string = transform_coordinate(origin, destination)
    
    url_dist = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=kilometers&origins={}&destinations={}&key={}'.format(string[0], string[1], key)
    
    r = requests.get(url_dist)  
    #return r.json()
    return r.json()['rows'][0]['elements'][0]['distance']['value']/1000, round(r.json()['rows'][0]['elements'][0]['duration']['value']/60,2)
    
    
    
def get_direction(origin, destination, key):
    """
    This function takes as input:
    - origin coordinates tuple
    - destination coordinates tuple
    - API key 
    
    return:
    - Google Maps API JSON answer
    """
    string = transform_coordinate(origin, destination)
    url_dist = 'https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&key={}'.format(string[0], string[1], key)
    
    r = requests.get(url_dist) 
    return r.json() 
 


def filter_no_gas(x):
    """
    used to filter station without gas
    """
    if not(type(x)) == float:
        return None
    else:
        return x

    
def get_cost_filling(gas_price, volume_gas_needed, car_consumption, real_distance):
    """
    this function takes as input:
    - gas price (in €/liters)
    - needed volume of gas (in liters)
    - car consumption (in liters/100km)
    - real distance(computed by google api)(in km)
    
    it returns:
    - the cost of filling up the car: gas + round trip
    """
    try:
        #2 times because round trip
        return gas_price*volume_gas_needed + 2*car_consumption/100*real_distance
    except:
        #if there is no gas of this type at the station, then it makes this point as an outfitter
        return 1000000
    
    
    

def plot_stations(df, key, top_N = 3, M_following = 7, scale = 4):
    
#     sns.set(style="white")
#     fig,(ax) = plt.subplots()
#     plt.title('Map of the Home - Stations')
#     plt.plot([0],[0], color = 'blue', label = 'bottomly ranked stations')
#     plt.plot([0],[0], color = 'green', label = 'regulary ranked stations')
#     plt.plot([0],[0], color = 'yellow', label = 'Highly ranked stations')
#     plt.plot([0],[0], color = 'red', label = 'best stations')
    
#     plt.legend(loc='upper right', bbox_to_anchor=(1.6, 1), s)
#     plt.show()
    
    
    gmaps.configure(api_key=key) # Your Google API key

    gmap = gmaps.figure(center = current_coordinates, zoom_level = 11)
    
    #current point layer
    marker_location = [current_coordinates]
    markers_layer = gmaps.marker_layer(marker_location)
    gmap.add_layer(markers_layer)
    
    #best layer
    df_ = df.iloc[0:1, :][['latitude', 'longitude']]
    top_layer = gmaps.symbol_layer(
        df_, fill_color="red", stroke_color="red", scale=scale)
    gmap.add_layer(top_layer)
    
    #top layerN
    df_ = df.iloc[1:1+top_N, :][['latitude', 'longitude']]
    top_layer = gmaps.symbol_layer(
        df_, fill_color="yellow", stroke_color="yellow", scale=scale)
    gmap.add_layer(top_layer)
    
    #M following layer
    df_ = df.iloc[1+ top_N:1+top_N + M_following, :][['latitude', 'longitude']]
    next_layer = gmaps.symbol_layer(
        df_, fill_color="green", stroke_color="green", scale=scale)
    gmap.add_layer(next_layer)
    
    #remaining layer
    df_ = df.iloc[1+top_N + M_following:, :][['latitude', 'longitude']]
    other_layer = gmaps.symbol_layer(
        df_, fill_color="blue", stroke_color="blue", scale=scale)
    gmap.add_layer(other_layer)

    display(gmap)

    return gmap
    
    


def plot_itinary(itinary, key):
    gmaps.configure(api_key=key)
    # Request directions via public transit


    fig = gmaps.figure()
    itinary_plot = gmaps.directions_layer(
            itinary[0], itinary[-1],  waypoints=itinary[1:-1], 
            travel_mode='DRIVING')
    fig.add_layer(itinary_plot)
    
    display(fig)  
    embed_minimal_html('./outputs/itinary_plot.html', views=[fig])
    
    
def get_summary_gas_station(df, current_coordinates,new_key, type_):
    if type_ == 'cheaper':
        by_ = 'cost_filling_and_trip'
    elif type_ == 'closer':
        by_ = 'real_time_minute'
    elif type_ == 'optimum':
        by_ = 'adjusted_cost_filling_and_trip'
    else:
        by_ = 'gas_price'
        
        
    df.sort_values(by = by_, ascending=True, inplace=True)
    #get the direction on google API
    x = get_direction(current_coordinates, (df['latitude'].tolist()[0], 
                                            df['longitude'].tolist()[0]), new_key)

    #get summary informations
    summary_distance = x['routes'][0]['legs'][0]['distance']['text']
    summary_duration = x['routes'][0]['legs'][0]['duration']['text']
    departure_point = x['routes'][0]['legs'][0]['start_adress']
    end_point = x['routes'][0]['legs'][0]['end_adress']
    best_station_id = df['id'].tolist()[0]
    cost_filling = round(df['cost_filling'].tolist()[0],2)
    cost_filling_and_trip = round(df['cost_filling_and_trip'].tolist()[0],2)
    adjusted_cost_filling_and_trip = round(df['adjusted_cost_filling_and_trip'].tolist()[0],2)
    gas_price = round(df['gas_price'].tolist()[0],2)
    coordinates_station = (df['latitude'].tolist()[0], df['longitude'].tolist()[0])

    df_summary = pd.DataFrame([summary_distance, summary_duration,
                               departure_point, end_point, coordinates_station, 
                               best_station_id, cost_filling,
                              cost_filling_and_trip, adjusted_cost_filling_and_trip, gas_price], index = ['summary_distance', 'summary_duration', 
                                                                     'departure_point', 'end_point', 'coordinates_station', 
                                                                        'best_station_id', 'cost_filling',
                                                                'cost_filling_and_trip', 'adjusted_cost_filling_and_trip', 'gas_price'], columns = ['Info'])

    df_summary.to_csv('./outputs/df_summary_{}.csv'.format(type_))
    
    return df_summary, summary_distance, summary_duration, departure_point, end_point
        
    
    
def get_road(df,type_, current_coordinates, key):
    print('go')
    
    if type_ == 'cheapest':
        by_ = 'cost_filling_and_trip'
    elif type_ == 'closest':
        by_ ='real_time_minute'
    else:
        by_ = 'adjusted_cost_filling_and_trip'
        
    df.sort_values(by = by_, ascending=True, inplace=True)
    #get the direction on google API
    x = get_direction(current_coordinates, (df['latitude'].tolist()[0], 
                                            df['longitude'].tolist()[0]), key)
    
    
    #all the steps on the road
    list_steps = x['routes'][0]['legs'][0]['steps']

    #store all the steps into a dataframe
    df_road = pd.DataFrame(columns = [ 'start_coordinates', 'end_coordinates', 'duration',
                                      'distance', 'instruction', 'step'], index = np.arange(len(list_steps)))


    for i in range(len(list_steps)):
        step = 'STEP_'+chr(65+i)
        start_coordinates = (list_steps[i]['start_location']['lat'], list_steps[i]['start_location']['lng'])
        end_coordinates = (list_steps[i]['end_location']['lat'], list_steps[i]['start_location']['lng'])
        duration = list_steps[i]['duration']['text']
        distance = list_steps[i]['distance']['text']
        instruction = list_steps[i]['html_instructions']#.split('<div')[0].replace('<b>', '').replace('</b>', '')
        table = [start_coordinates, end_coordinates, duration, distance, instruction, step]
        df_road.iloc[i,:] = np.array(table)


    
    return df_road
    
    



    