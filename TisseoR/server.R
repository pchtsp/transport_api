library(shiny)
library(leaflet)
library(RColorBrewer)
library(data.table)

source('functions.R')
min_hour = '08:00:00'
max_hour = '09:00:00'
directory <- 'C:\\Users\\pchtsp\\Documents\\projects\\demo\\transport_api\\data_tisseo\\tisseo_gtfs\\'
response <- tisseo$get_lats_longs_from_node(directory, trip='4503603929131499', sequence = '8', min_hour=min_hour, max_hour=max_hour)
data.table(lat=lats)
# tables <- tisseo$get_tables(directory)
# info <- tisseo$get_info_object(tables, min_hour=min_hour, max_hour=max_hour)
# default_stop <- tisseo$Node(trip_id='4503603929131499',stop_sequence=8, info=info)
# arcs <- tisseo$graph_from_node(default_stop, max_hour=max_hour)


function(input, output, clientData, session) {
    
    output$map <- renderLeaflet({
        leaflet(splines) %>% 
            addProviderTiles("CartoDB.DarkMatterNoLabels") %>% 
            addPolylines(opacity = 0.4, 
                         weight = 3, 
                         color = c("#ffff00", "#ff4f00", "#3fff00", "#ffaa00", "#A4ff00")) %>% 
            addMarkers(lat= latlong$lat, lng= latlong$lon)
    })
    
}