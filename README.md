# Pollution Dashboard

This project visualizes air pollution data in Madrid using Dash and Plotly.

Visualisation is available here : https://dataviz-5zhh.onrender.com/

`data_prep_day.py` : Prepares the dataset extracted from the `VDS2425_Madrid.zip` file.

`app.py` : Implements various visualizations using Dash and Plotly.

`requirements.txt` Lists the dependencies required to run the app on OnRender.

`informacion_estaciones_red_calidad_aire.csv`: is pulled from website of [Madrid](https://datos.madrid.es/sites/v/index.jsp?vgnextoid=9e42c176313eb410VgnVCM1000000b205a0aRCRD&vgnextchannel=374512b9ace9f310VgnVCM100000171f5a0aRCRD) to merge stations into areas.

Pollutant thresholds are taken from the Special report 02/2025: Urban pollution in the EU – Cities have cleaner air but are still too noisy, available [here](https://www.eca.europa.eu/en/publications?ref=SR-2025-02).

The Assets folder contains the CSS sheet and the logo of Madrid.
