library(shiny)
library(leaflet)
library(RColorBrewer)
library(data.table)
library(htmltools)
library(stringr)

source('functions.R')

def_data <- 
    list(
        min_hour = '08:00:00'
        ,max_hour = '09:00:00'
        ,trip_id = '4503603929131499'
        ,stop_seq = '8'
    )

directory <- 'data_tisseo\\tisseo_gtfs\\'
# browser()
def_data$tisseo <- get_tisseo_nodes()
def_data$tables <- def_data$tisseo$get_tables(directory)
def_data$info <- def_data$tisseo$get_info_object(def_data$tables, 
                                                 min_hour=def_data$min_hour, 
                                                 max_hour=def_data$max_hour)

result <- do.call(get_graph_from_stop, args=def_data)
# this works.
# result <- iterate(arcs[default_stop]$keys())
function(input, output, clientData, session) {
    
    output$map <- renderLeaflet({
        leaflet(result$table) %>% 
            addProviderTiles("CartoDB.DarkMatterNoLabels") %>% 
            addCircles(lat= ~lat, lng= ~long, radius=~radius,
                       fillOpacity = 0.05, weight=1) %>%
            addPolylines(data=result$lines, lng=~long, lat=~lat, 
                         color = c("#ffff00", "#ff4f00", "#3fff00", "#ffaa00", "#A4ff00"))
    })
    
    observe({
        temp <- input$map_click
        if (temp %>% is.null){
            return()
        }
        # find stops aroung the click.
        # browser()
        stop_ids <- 
            def_data$info$stop_times_2 %>% 
            select(stop_id= stop_id_backup) %>% 
            distinct(stop_id)
        stops <- 
            def_data$tables$stops %>% 
            inner_join(stop_ids) %>% 
            mutate(lat = stop_lat %>% as.numeric,
                   long=stop_lon %>% as.numeric) %>% 
            mutate(dist = abs(lat-temp$lat)+abs(long-temp$lng)) %>% 
            filter(dist < 0.005) %>% 
            select(lat, long, stop_id)
        
        # layerId
        # here, we want to just add a marker
        leafletProxy("map", data = stops) %>%
            clearMarkers() %>% 
            addMarkers(lat= ~lat, lng= ~long, layerId = ~stop_id)
        
    })
    
    observe({
        # colorBy <- input$color
        temp <- input$map_marker_click
        if (temp %>% is.null){
            return()
        }
        # browser()
        # date_min_hour <- sprintf('1900-01-01 %s', def_data$min_hour)
        first_node <- 
            def_data$info$stop_times_2 %>% 
            filter(stop_id_backup==temp$id) %>% 
            arrange(arrival_time) %>% 
            slice(1)
        
        if (nrow(first_node) == 0){
            return()
        }
        def_data$trip_id <- first_node$trip_id
        def_data$stop_seq <- first_node$stop_sequence
        
        result <- do.call(get_graph_from_stop, args=def_data)
        
        leafletProxy("map", data = result$table) %>%
            clearShapes() %>%
            addCircles(lat= ~lat, lng= ~long, radius=~radius,
                       fillOpacity = 0.05, weight=1) %>%
            addPolylines(data=result$lines, lng=~long, lat=~lat, 
                         color = c("#ffff00", "#ff4f00", "#3fff00", "#ffaa00", "#A4ff00"))
    })
    
}