library(tidyverse)
library(reticulate)
library(magrittr)

get_python_module <- function(rel_path, name){
    # this will work as a proxy for shinyapps. maybe.
    # py_install(c('pandas', 'pytups'), python_version=3)
    if(.Platform$OS.type == "unix") {
        use_virtualenv('transport_api', required = TRUE)
    } else {
        paths <- 'c:/Anaconda3/Scripts/conda.exe'
        use_condaenv('transport_api', conda=paths, required=TRUE)
    }
    py_discover_config()
    script <- import_from_path(name, path=getwd())
    script
}

get_tisseo_nodes <- function() get_python_module('', 'analize_tisseo')

default_data <- function(){
    list(
        min_hour = '08:00:00'
        ,max_hour = '09:00:00'
        ,trip_id = '4503603929131499'
        ,stop_seq = '8'
        ,day_of_week = 'monday'
        ,max_dist_km_walk=0.1
    )
    
}

get_info <- function(data){
    data$tisseo$get_info_object(
        data$tables, 
        min_hour=data$min_hour, 
        max_hour=data$max_hour,
        day_of_week =data$day_of_week,
        max_dist_km_walk = data$max_dist_km_walk)
}

get_graph_from_stop <- function(min_hour, max_hour, trip_id, stop_seq, tisseo, tables, info, ...){
    default_stop <- tisseo$Node(trip_id=trip_id,stop_sequence=stop_seq, info=info)
    arcs <- tisseo$graph_from_node(default_stop, max_hour=max_hour)
    if (arcs %>% length %>% equals(0)){
        return(list(table=data.frame(), lines=data.frame()))
    }
    # browser()
    table <- 
        tisseo$get_lats_longs(arcs, info) %>% 
        arrange(time) %>% 
        distinct(lat, long, route, .keep_all = TRUE) %>% 
        mutate(popup = sprintf("<b>%s</b><br/>Hour:%s<br/>Line:%s", name, time, route),
               seconds= as.ITime(max_hour) - as.ITime(time),
               radius = (as.integer(seconds)/3.6))
    
    colors <- c("#ffff00", "#ff4f00", "#3fff00", "#ffaa00", "#A4ff00")
    
    # browser()
    last_rows <- 
        table %>% distinct(trip) %>% 
        mutate(seq= 10000, lat=NA, long=NA, seconds=-100)
    route_color <- 
        last_rows %>% select(trip) %>% 
        mutate(color = rep_len(colors, nrow(.)))
    polylines <- 
        table %>% 
        select(trip, seq, lat, long, seconds) %>% 
        bind_rows(last_rows) %>%  
        arrange(trip, seq) %>% 
        distinct(lat, long, trip, seconds) %>% 
        left_join(route_color)
    
    return(list(table=table, lines=polylines))
    
}

update_map <- function(data){
    result <- do.call(get_graph_from_stop, args=data)
    
    leafletProxy("map", data = result$table) %>%
        clearShapes() %>%
        addCircles(lat= ~lat, lng= ~long, radius=~radius,
                   fillOpacity = 0.05, weight=1) %>%
        addPolylines(data=result$lines, lng=~long, lat=~lat, 
                     color = c("#ffff00", "#ff4f00", "#3fff00", "#ffaa00", "#A4ff00"))
}
