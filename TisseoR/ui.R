library(leaflet)
library(shiny)

bootstrapPage(
    tags$style(type = "text/css", "html, body {width:100%;height:100%}"),
    h2("Exploring Toulouse"),
    leafletOutput("map", width="100%", height="100%")
)
