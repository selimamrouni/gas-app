
# coding: utf-8

# In[ ]:


from flask import Flask, request, render_template, url_for, flash, session
import gasApp_backend
import pandas as pd

from utilz import *


#this is the google API key which is stored in the py backend script
new_key = gasApp_backend.new_key

from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map

app = Flask(__name__, static_folder="./static/css", template_folder="./templates")

# you can set key as config
app.config['GOOGLEMAPS_KEY'] = new_key

# Initialize the extension
GoogleMaps(app)

# secret key is needed for session
#this is randomly generated
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa5'



@app.route('/')
def home():
        return render_template('home.html')

@app.route('/getform/',methods=['POST','GET'])
def get_form():
    if request.method=='POST':
        return render_template('form.html')
    


@app.route('/getinfo/',methods=['POST','GET'])
def get_info():
    if request.method=='POST':
        result=request.form        
        street = result['street']    
        number = result['number']    
        zip_ = result['zip']    
        city = result['city']   
        adress = '{} {}, {}, {}'.format(number, street, zip_, city)
        country = result['country']
        beeline = float(result['beeline'])    
        gas_type = result['gas_type']    
        volume = float(result['volume'])   
        consumption = float(result['consumption'])
        time_value = float(result['time_value'])
        
        
        #current coordinates of the current adress
        current_coordinates = gasApp_backend.get_current_coordinate(adress, new_key, country)
        
        #store the current coordinate
        session['current_coordinates'] = current_coordinates
        
        
        df_station = gasApp_backend.get_station_data(adress,country, 
                                                     beeline,time_value, gas_type, volume, consumption)
        
        print(df_station)
        
        #can't store as a session object dataframe df_station
        #need to be converted to json first
        session['df_station'] = df_station.to_json()
        #save to be used later
        #df_station.to_csv('./outputs/df_station.csv')
        
        list_dic_other_station = list()

        list_station = df_station.id


        for i in range(len(df_station)):
            #if list_station[i] in [dic_cheaper['Station Name'], dic_closer['Station Name'], dic_optimum['Station Name']]:
            #    pass
           # else:

            df_ = df_station.set_index('id').copy()
            dict_ = dict()

            dict_['Station Name'] = list_station[i]
            dict_['Distance'] = df_.loc[list_station[i], 'real_distance_km']
            dict_['Time To Go'] = df_.loc[list_station[i], 'real_time_minute']
            dict_['Gas Price'] = df_.loc[list_station[i], 'gas_price']
            dict_['Cost Tank Filling & Round-Trip'] = df_.loc[list_station[i], 'cost_filling_and_trip']
            dict_['all costs']= df_.loc[list_station[i], 'adjusted_cost_filling_and_trip']
            dict_['coordinates'] = (df_.loc[list_station[i], 'latitude'], df_.loc[list_station[i], 'longitude'])
            dict_['adress_station'] = df_.loc[list_station[i], 'adress']
            list_dic_other_station.append(dict_)

        dic_cheapest = sorted(list_dic_other_station, key=lambda k: k['Cost Tank Filling & Round-Trip'])[0]
        dic_closest = sorted(list_dic_other_station, key=lambda k: k['Time To Go'])[0]
        dic_optimum = sorted(list_dic_other_station, key=lambda k: k['all costs'])[0]
        
        dic_pricest = sorted(list_dic_other_station, key=lambda k: k['Cost Tank Filling & Round-Trip'])[-1]
        print(dic_pricest)
        
        #store the dictionnary
        session['dic_cheapest'] = dic_cheapest
        session['dic_closest'] = dic_closest
        session['dic_optimum'] = dic_optimum
        session['dic_pricest'] = dic_pricest

        try:
            list_dic_other_station.remove(dic_cheapest)
        except:
            print('dic cheapest already removed')

        try:
            list_dic_other_station.remove(dic_closest)
        except:
            print('dic_closest already removed')

        try:
            list_dic_other_station.remove(dic_optimum)
        except:
            print('dic_optimum already removed')
            
        try:
            list_dic_other_station.remove(dic_pricest)
        except:
            print('dic_pricest already removed')
        
        #list of dictionaries to plot all the points
        
        #list of all the other points 
        #non-highlighted gas stations
        
        #nice markers hre : https://sites.google.com/site/gmapsdevelopment/
        #or here: https://github.com/rochacbruno/Flask-GoogleMaps/blob/master/flask_googlemaps/icons.py
        #or here: http://tancro.e-central.tv/grandmaster/markers/google-icons/
        list_marker =  [   
              {
                 'icon': 'http://maps.gstatic.com/mapfiles/ridefinder-images/mm_20_gray.png',
                 'lat': dic['coordinates'][0],
                 'lng': dic['coordinates'][1],
                 'infobox': """<b>Other Station</b><br><u>Gas Price:</u> {} €/L<br><u>Distance:</u> {} Km<br><u>Time To Go:</u> {} min<br><u>Tank Filling Cost:</u> {} €<br><u>Adress:</u> {}""".format(dic['Gas Price'], dic['Distance'],
                          dic['Time To Go'],dic['Cost Tank Filling & Round-Trip'], dic['adress_station'])
              } for dic in list_dic_other_station]
        print(list_marker)
        
        #current position marker 
        list_marker +=               [{
                 'lat': current_coordinates[0],
                 'lng': current_coordinates[1],
                 'infobox': """<b>Current Position</b>"""
                  
              }]
        #cheapest marker
        list_marker += [{
                 'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                 'lat': dic_cheapest['coordinates'][0],
                 'lng': dic_cheapest['coordinates'][1],
                 'infobox': """<b>Cheapest</b><br><u>Gas Price:</u> {} €/L<br><u>Distance:</u> {} Km<br><u>Time To Go:</u> {} min<br><u>Tank Filling Cost:</u> {} €<br><u>Adress:</u> {}""".format(dic_cheapest['Gas Price'], dic_cheapest['Distance'],
                          dic_cheapest['Time To Go'],dic_cheapest['Cost Tank Filling & Round-Trip'], dic_cheapest['adress_station'])
              }]
        #pricest marker
        list_marker += [{
                 'icon': 'http://maps.google.com/mapfiles/ms/icons/purple-dot.png',
                 'lat': dic_pricest['coordinates'][0],
                 'lng': dic_pricest['coordinates'][1],
                 'infobox': """<b>Pricest</b><br><u>Gas Price:</u> {} €/L<br><u>Distance:</u> {} Km<br><u>Time To Go:</u> {} min<br><u>Tank Filling Cost:</u> {} €<br><u>Adress:</u> {}""".format(dic_pricest['Gas Price'], dic_pricest['Distance'],
                          dic_pricest['Time To Go'],dic_pricest['Cost Tank Filling & Round-Trip'], dic_pricest['adress_station'])
              }]
        #closest marker
        list_marker += [{
                 'icon': 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png',
                 'lat': dic_closest['coordinates'][0],
                 'lng': dic_closest['coordinates'][1],
                 'infobox': """<b>Closest</b><br><u>Gas Price:</u> {} €/L<br><u>Distance:</u> {} Km<br><u>Time To Go:</u> {} min<br><u>Tank Filling Cost:</u> {} €<br><u>Adress:</u> {}""".format(dic_closest['Gas Price'], dic_closest['Distance'],
                          dic_closest['Time To Go'],dic_closest['Cost Tank Filling & Round-Trip'], dic_closest['adress_station'])
              }]
        #optimum marker
        list_marker += [{
                 'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
                 'lat': dic_optimum['coordinates'][0],
                 'lng': dic_optimum['coordinates'][1],
                 'infobox': """<b>Optimum</b><br><u>Gas Price:</u> {} €/L<br><u>Distance:</u> {} Km<br><u>Time To Go:</u> {} min<br><u>Tank Filling Cost:</u> {} €<br><u>Adress:</u> {}""".format(dic_optimum['Gas Price'], dic_optimum['Distance'],
                          dic_optimum['Time To Go'],dic_optimum['Cost Tank Filling & Round-Trip'], dic_optimum['adress_station'])
              }]
        #plot the beeline 
        circles=[{
            'stroke_color': '#FF00FF',
            'stroke_opacity': 0.5,
            'stroke_weight': 3,
            'fill_color': '#FF00FF',
            'fill_opacity': 0.05,
            'center': {
                'lat': current_coordinates[0],
                'lng': current_coordinates[1]
            },
            'radius': 1000*int(beeline),
            'infobox': "This is the beeline area."
        }]
        
        #plot the map part
        mymap = Map(
            identifier="maps_highlighted_stations",
            lat=current_coordinates[0],
            lng=current_coordinates[1],
            zoom = 13,
            style = 'height: 600px; width :800px; margin-left:auto; margin-right:auto;',
            
            circles = circles,
            markers= list_marker,
            

        )
        
        dic_optimum['savings'] = round(dic_pricest['Cost Tank Filling & Round-Trip'] - dic_optimum['Cost Tank Filling & Round-Trip'],2)
        dic_cheapest['savings'] = round(dic_pricest['Cost Tank Filling & Round-Trip'] - dic_cheapest['Cost Tank Filling & Round-Trip'] ,2)
        dic_closest['savings'] = round(dic_pricest['Cost Tank Filling & Round-Trip'] - dic_closest['Cost Tank Filling & Round-Trip'],2)  
        dic_pricest['savings'] = round(dic_pricest['Cost Tank Filling & Round-Trip'] - dic_pricest['Cost Tank Filling & Round-Trip'],2)  
        
        
        best_savings = dic_cheapest['savings']
        print('dic optimum')
        print(dic_optimum)


        return render_template('result.html', prediction = 2, dic_cheapest = dic_cheapest,
                              dic_closest = dic_closest, dic_optimum= dic_optimum,dic_pricest = dic_pricest, best_savings = best_savings,
                              mymap=mymap)



@app.route('/getdirection/',methods=['POST','GET'])
def get_direction():    
    if request.method=='POST':
        
        #load current coordinates of the current adress
        current_coordinates = session['current_coordinates']
        
        #load the summary of all the stations
        #read from a json file
        df_station = pd.read_json(session['df_station'])
        
        result=request.form 
        
        if result['go_direction'] == 'Cheapest':
            #get the path to go to the designated station
            df_road = get_road(df_station,'cheapest', current_coordinates, new_key)
            #load gas station informations
            dict_station = session['dic_cheapest']
            
        elif result['go_direction'] == 'Closest':
            df_road = get_road(df_station,'closest', current_coordinates, new_key)
            dict_station = session['dic_closest']
        else:
            df_road = get_road(df_station,'other', current_coordinates, new_key)
            dict_station = session['dic_optimum']
            
        
        
        list_marker = list()
        list_path = list()
        #list of all the steps
        for i in range(len(df_road)):
            step = df_road.iloc[i, 5]
            print(step)
            lat = df_road.iloc[i, 0][0]
            lon = df_road.iloc[i, 0][1]
            distance = df_road.iloc[i, 2]
            duration = df_road.iloc[i, 3]
            instruction = df_road.iloc[i, 4]
            
            list_marker += [{
                     'icon': 'https://www.google.com/mapfiles/marker{}.png'.format(step.split('_')[1]),
                     'lat': lat,
                     'lng': lon,
                     'infobox': """<b>{}</b><br><u>Distance:</u> {}<br><u>Duration:</u> {}<br><u>Instruction:</u> {}<br>""".format(step, distance,
                              duration,instruction)
                  }] 
            
            list_path += [{'lat': lat, 'lng': lon}]


        #add the gas station to the path
        list_path += [{'lat': dict_station['coordinates'][0], 'lng': dict_station['coordinates'][1]}]

        
        #line of the road 
        polyline = {
        'stroke_color': '#0AB0DE',
        'stroke_opacity': 1.0,
        'stroke_weight': 3,
        'path': list_path}
        
        
            
        lat_departure = df_road.iloc[0, 0][0]
        lon_departure = df_road.iloc[0, 0][1]
        
        lat_arrival = dict_station['coordinates'][0]
        lon_arrival = dict_station['coordinates'][1]
        
        lat_center = (lat_departure + lat_arrival)/2
        lon_center = (lon_departure + lon_arrival)/2
        
        #add the gas station marker
        
        
            
        list_marker += [{
                 'icon': 'http://maps.google.com/mapfiles/kml/pal2/icon21.png',
                 'lat': lat_arrival,
                 'lng': lon_arrival,
                 'infobox': """<b>Station</b><br><u>Gas Price:</u> {} €/L<br><u>Distance:</u> {} Km<br><u>Time To Go:</u> {} min<br><u>Tank Filling Cost:</u> {} €""".format(dict_station['Gas Price'], dict_station['Distance'],
                          dict_station['Time To Go'],dict_station['Cost Tank Filling & Round-Trip'])

              }] 
        
        
        #plot the map part
        mymap = Map(
            identifier="maps_road",
            lat=lat_center,
            lng=lon_center,
            zoom = 14,
            #style = "height:500px;width:500px;margin:0;",
            style = 'height: 600px; width :800px; margin-left:auto; margin-right:auto;',
            markers= list_marker,
            polylines = [polyline],

        )
        
        #get dictionnary of the instructions to plot it in webpage
        dict_road = dict()
        for i in range(len(df_road)):
            step = df_road['step'][i]
            instruction = df_road['instruction'][i]
            distance = df_road['distance'][i]
            duration = df_road['duration'][i]
            
            cleaned_instruction = instruction.split('<div')[0].replace('<b>', '').replace('</b>', '') + ' ' 
            
            try:
                cleaned_instruction += instruction.split('div>')[1].replace('<b>', '').replace('</b>', '')
            except:
                pass
            
            dict_road[step] = 'During {} and {} - '.format(distance, duration) + cleaned_instruction
            
    
    
        return render_template('direction.html', dict_road = dict_road, mymap=mymap)  
    
    
    
    
    
    
if __name__ == '__main__':
    #app.debug = True
    app.run()

