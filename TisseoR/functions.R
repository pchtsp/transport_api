library(tidyverse)
library(reticulate)

get_python_module <- function(rel_path, name){
    use_condaenv('transport_api', conda='c:/Anaconda3/Scripts/conda.exe', required=TRUE)
    # use_virtualenv('~/Documents/projects/OPTIMA/python/venv/', required = TRUE)
    py_discover_config()
    sysp = import('sys')
    opt_path = ''
    python_path <- '%s/%s../transport_api/' %>% sprintf(getwd(), opt_path)
    print(python_path)
    sysp$path <- c(python_path, sysp$path)
    scripts_path = paste0(python_path, rel_path)
    script <- import_from_path(name, path=scripts_path)
    script
}

get_tisseo_nodes <- function() get_python_module('scripts', 'analize_tisseo')

tisseo <- get_tisseo_nodes()