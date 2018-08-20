import pandas as pd
import numpy as np

from zipfile import ZipFile
import urllib.request
import xml.etree.cElementTree as et
from zipfile import ZipFile
#haversine distance
from haversine import haversine
import requests
import googlemaps


    
from utilz import *

#url to get the gas station data
url = 'https://donnees.roulez-eco.fr/opendata/instantane' 

#google key 
#please replace with yours
new_key = 'AIzaSyAW_w-YdEODRioT4rx6u9wiqKY6z3iWhaU'





def get_station_data(current_address, country, beeline_max, time_value, gas_type, volume_gas_needed, car_consumption):

    print('Get coordinates')
    current_coordinates = get_current_coordinate(current_address, new_key,'France')


    print('Beginning file download with urllib2...')

    print('Beginning file download with urllib2...')
    #try to avoid data provider down
    try: 
        urllib.request.urlretrieve(url, './data/zipData.zip') 
    except:
        
        print('open data down :(')

     
    # specifying the zip file name
    file_name = 'zipData.zip'
     
    # opening the zip file in READ mode
    with ZipFile('./data/' + file_name, 'r') as zip:
        # printing all the contents of the zip file
        zip.printdir()
        name_unzipped = zip.infolist()[0].filename
        # extracting all the files
        print('Extracting all the files now...')
        zip.extractall('./data/')
        print('Done!')


    print('retrieve information')
    parsedXML = et.parse( './data/PrixCarburants_instantane.xml' )

    df_station = pd.DataFrame(columns = ['id', 'adress', 'latitude', 'longitude', 'dictionnary_gas', 'beeline'],
                              index = np.arange(len(parsedXML.getroot())) )
    c_error = 0
    c_within = 0
    c_without = 0

    for node in tqdm(parsedXML.getroot()):
        try:
            
            
            #coordinates of the station  
            latitude  = node.attrib.get('latitude')
            #converstion from PTV_GEODECIMAL to standard geodecimal WGS8
            latitude = float(latitude)/100000
            longitude  = node.attrib.get('longitude')
            #converstion from PTV_GEODECIMAL to standard geodecimal WGS8
            longitude = float(longitude)/100000

            #compute beeline distance between stations and current_address
            distance = get_haversine(current_coordinates, (latitude, longitude))

            if distance <= beeline_max:
                #store only the data of incircle stations

                #id of the station
                id_ = node.attrib.get('id')

                #adress of the station
                adress = node.find('adresse').text
                zip_code = node.attrib.get('cp')
                city = node.find('ville').text
                full_address = adress + ', ' + zip_code + ', ' + city

                #store gas data in dictionnary 
                #the type of gas are different and not structured in the xml file 
                dict_gas = dict()
                for p in node.findall('prix'):
                    dict_gas[p.attrib.get('nom')] = p.attrib.get('valeur')

                df_station.iloc[c_within,:] = [id_, full_address, latitude, longitude, dict_gas, distance]
                #pd.concat(df_station, pd.DataFrame([id_, address, latitude, longitude, dict_gas]))
                c_within+=1

            c_without+=1
                
        except:
            c_error +=1
            
    print(c_error, 'stations raised an error!')
    print(c_without, 'stations are outside of the admitted perimeter...')
    print(c_within, 'stations are inside of the admitted perimeter!')

    df_station.dropna(inplace = True)

    df_station['gas_price'] = df_station.apply(lambda x:get_gas_price(gas_type, x['dictionnary_gas']), axis = 1)
    df_station['filter'] = df_station.apply(lambda x:filter_no_gas(x['gas_price']), axis = 1)
    df_station = df_station.dropna().drop('filter', axis = 1)

    print('compute cost of filling')

    df_station['cost_filling'] = df_station.apply(lambda x: x.gas_price * volume_gas_needed, axis = 1)
    df_station.sort_values(by = 'cost_filling', inplace = True)
    df_station.reset_index(drop = True, inplace = True)

    print('compute cost filling including distance')

    df_station['api_request'] = df_station.apply(lambda x: get_distance_and_time(current_coordinates, 
                                                                         (x['latitude'], x['longitude']), new_key), axis =1)
    df_station['real_distance_km'] = df_station['api_request'].apply(lambda x:x[0])
    df_station['real_time_minute'] = df_station['api_request'].apply(lambda x:x[1])
    df_station['cost_filling_and_trip'] = df_station.apply(lambda x: round(get_cost_filling(x['gas_price'], volume_gas_needed, 
                                                                         car_consumption, x['real_distance_km']),2), axis = 1)
    df_station.sort_values(by = 'cost_filling_and_trip', inplace = True)

    print('compute cost filling including distance and time')

    df_station['adjusted_cost_filling_and_trip'] = df_station.apply(lambda x: x.cost_filling_and_trip + 2*time_value*x.real_time_minute, axis=1)
    df_station.sort_values(by = 'adjusted_cost_filling_and_trip', ascending=True, inplace=True)

    print('compute the summary of the 3 types of gas station')

    #df_summary_cheaper,_,_ ,_,_= get_summary_gas_station(df_station, current_coordinates,new_key, 'cheaper')

    #df_summary_closer, _,_,_,_ = get_summary_gas_station(df_station, current_coordinates,new_key, 'closer')

    #df_summary_optimum,  _,_,_,_  = get_summary_gas_station(df_station, current_coordinates,new_key, 'optimum')




    return df_station
