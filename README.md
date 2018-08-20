# gas-app
gas app web application

This repository presents a [web-app](https://gas-app-usa.herokuapp.com/) developed based on a discussion with my father to help him make saving on the tank-filling. 
Please, the app can takes some seconds to launch, this is due to Heroku which can be longer for free hosting.

You can check-out my [Medium Post](https://medium.com/@selimamrouni/leverage-french-government-open-data-to-make-savings-on-gas-tank-filling-b09ecc68a230) for more information. 

The main files are:
- gasApp_notebook.ipynb: original notebook where the pipeline has been developed 
- gasapp folder: this is the folder of the Flask app
  - utilz.py : useful functions 
  - gasApp_backend.py: backend of the application, wrap the useful functions into a wrapped function
  - app.py: Flask part, design the backend of the app 
  - data: folder in which the data scapped from the French open data website are stored 
  - output: folder in which data computed by the backend are stored
  - templates: html web pages folder
  - static: CSV files
