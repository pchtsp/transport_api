library(shiny)
library(leaflet)
library(RColorBrewer)
library(data.table)
library(htmltools)
library(stringr)

source('functions.R')

def_data <- default_data()

directory <- 'data_tisseo\\tisseo_gtfs\\'
# browser()
def_data$tisseo <- get_tisseo_nodes()

def_data$tables <- def_data$tisseo$get_tables(directory)

def_data$info <- get_info(def_data)
result <- do.call(get_graph_from_stop, args=def_data)

function(input, output, clientData, session) {
    
    # get all inputs into data object
    observeEvent(input$rerun, {
        # browser()
        def_data$day_of_week <<- input$day_of_week
        def_data$min_hour <<- input$min_hour %>% strftime("%T")
        def_data$max_hour <<- input$max_hour %>% strftime("%T")
        def_data$max_dist_km_walk <<- input$max_dist_km_walk
        def_data$info <<- get_info(def_data)
        update_map(def_data)
    })
    
    # create graph object
    output$map <- renderLeaflet({
        leaflet(result$table) %>% 
            addProviderTiles("CartoDB.DarkMatterNoLabels") %>% 
            addCircles(lat= ~lat, lng= ~long, radius=~radius,
                       fillOpacity = 0.05, weight=1) %>%
            addPolylines(data=result$lines, lng=~long, lat=~lat, 
                         color = c("#ffff00", "#ff4f00", "#3fff00", "#ffaa00", "#A4ff00"))
    })
    
    # get a click
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
        # print(def_data$day_of_week)
        
    })
    
    observe({
        # colorBy <- input$color
        temp <- input$map_marker_click
        if (temp %>% is.null){
            return()
        }
        # browser()
        first_node <- 
            def_data$info$stop_times_2 %>% 
            filter(stop_id_backup==temp$id) %>% 
            arrange(arrival_time) %>% 
            slice(1)
        
        if (nrow(first_node) == 0){
            return()
        }
        def_data$trip_id <<- first_node$trip_id
        def_data$stop_seq <<- first_node$stop_sequence
        
        # print(def_data$day_of_week)
        update_map(def_data)

    })
    
}