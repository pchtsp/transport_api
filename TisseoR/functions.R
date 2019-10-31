library(tidyverse)
library(reticulate)

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

get_graph_from_stop <- function(min_hour, max_hour, trip_id, stop_seq, tisseo, tables, info, ...){
    
    # browser()
    default_stop <- tisseo$Node(trip_id=trip_id,stop_sequence=stop_seq, info=info)
    arcs <- tisseo$graph_from_node(default_stop, max_hour=max_hour)
    table <- tisseo$get_lats_longs(arcs, info) %>% 
        arrange(time) %>% distinct(lat, long, route, .keep_all = TRUE) %>% 
        mutate(popup = sprintf("<b>%s</b><br/>Hour:%s<br/>Line:%s", name, time, route),
               seconds= as.ITime(max_hour) - as.ITime(time),
               radius = 1000*(as.integer(seconds)/3600))
    
    colors <- c("#ffff00", "#ff4f00", "#3fff00", "#ffaa00", "#A4ff00")
    
    last_rows <- 
        table %>% distinct(route) %>% 
        mutate(seconds= -100, lat=NA, long=NA)
    route_color <- 
        last_rows %>% select(route) %>% 
        mutate(color = rep_len(colors, nrow(.)))
    polylines <- table %>% select(route, seconds, lat, long) %>% 
        bind_rows(last_rows) %>%  arrange(route, -seconds) %>% 
        distinct(lat, long, route) %>% left_join(route_color)
    
    return(list(table=table, lines=polylines))
    
}
