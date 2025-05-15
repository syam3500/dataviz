# Pollution Dashboard

This project visualizes air pollution data in Madrid using Dash and Plotly[^1].

Visualisation is available here : https://dataviz-5zhh.onrender.com/, and it is deployed with Render[^2].

`data_prep_day.py` : Prepares the dataset extracted from the `VDS2425_Madrid.zip` file.

`avg_data_day.csv` : csv file created by the `data_prep_day.py` and data in that csv file is used to make the visualisations.

`app.py` : Implements various visualizations using Dash and Plotly.

`requirements.txt` Lists the dependencies required to run the app on OnRender.

`informacion_estaciones_red_calidad_aire.csv`: is pulled from website of [Madrid](https://datos.madrid.es/sites/v/index.jsp?vgnextoid=9e42c176313eb410VgnVCM1000000b205a0aRCRD&vgnextchannel=374512b9ace9f310VgnVCM100000171f5a0aRCRD) to merge stations into areas[^3].

The `Assets` folder contains the CSS sheet and the logo of Madrid.

Pollutant thresholds are taken from the Special report 02/2025: Urban pollution in the EU [^4].

Storytelling video is available [here](https://youtu.be/OPS1QL2AqVE).<br/>
<br/>

References: 
[^1]: DASH Documentation & User Guide | Plotly. https://dash.plotly.com/
[^2]: Cloud Application Platform |Render. https://render.com/
[^3]: Calidad del aire. Estaciones de control - Portal de datos abiertos del Ayuntamiento de Madrid. https://datos.madrid.es/sites/v/index.jsp? 
  vgnextoid=9e42c176313eb410VgnVCM1000000b205a0aRCRD&vgnextchannel=374512b9ace9f310VgnVCM100000171f5a0aRCRD
[^4]: Special report 02/2025: Urban pollution in the EU. European Court of Auditors. https://www.eca.europa.eu/en/publications?ref=SR-2025-02

