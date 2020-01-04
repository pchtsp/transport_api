library(leaflet)
library(shiny)
library(shinyTime)

source('functions.R')

all_weekdays <- c('monday', 'tuesday', 'wednesday', 
               'thursday', 'friday', 'saturday', 'sunday')

def_data <- default_data()

fluidPage(
    sidebarLayout(
        sidebarPanel(
            timeInput("min_hour", "Start:", seconds = FALSE, minute.steps = 15, 
                      value=strptime(def_data$min_hour, "%T", tz='CEST')),
            timeInput("max_hour", "End:", seconds = FALSE, minute.steps = 15, 
                      value=strptime(def_data$max_hour, "%T", tz='CEST')),
            numericInput(inputId='max_dist_km_walk', label='Max distance for exchange (km):', 
                         value=def_data$max_dist_km_walk),
            selectInput(
                'day_of_week', 'Select a day of the week',
                choices = all_weekdays,
                selected=def_data$day_of_week
            ),
            actionButton("rerun", "recalculate")
            
        ), 
        mainPanel(
            tags$style(type = "text/css", "html, body {width:100%;height:100%}"),
            leafletOutput("map")
        )
    )
)
