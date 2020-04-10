import requests
import pandas as pd
import re
from bs4 import BeautifulSoup

class RecipesScraper():

    def __init__(self):
        #Inicializa el objecto RecipesScraper
        self.url = "https://www.recetasgratis.net"
        self.data = pd.DataFrame(columns=['Id','Categoria','Nombre','Valoracion','Dificultad','NumComensales','Tiempo','Tipo','Descripcion', 'Link_receta'])

    def __download_html(self, url):
        #Decarga una página HTML y la devuelve
        return requests.get(url).text

    def __download_html_and_parse(self, url):
        #Decarga una página HTML, la parsea, y la devuelve
        return BeautifulSoup(self.__download_html(url), 'html.parser')

    def __get_recipes_category_info(self, bs):
        #Devuelve lista de tuples [(nombre_cat1, link1), (nombre_cat2, link2)]
        categories = []
        #Obtenemos categorias principales en las que se clasifican las recetas
        div_categories = bs.findAll("div", {"class": "categoria ga", "data-category":"Portada"})
        #Iteramos cada categoria para obtener: link y nombre de la categoria
        for div_category in div_categories:
            a_category = div_category.findAll("a", {"class":"titulo"})
            for link in a_category:
                categories.append((link.getText(), link.attrs["href"]))
        return categories

    def __get_next_page_link(self, bs):
        #Devuelve un string con la url a la siguiente pagina. En caso de no existir devuelve None
        div_paginator = bs.find("div", {"class": "paginator"})
        a_next_page = div_paginator.find("span", {"class":"current"}).find_next_sibling("a")
        if (a_next_page is not None):
            return a_next_page.attrs["href"]
        return None

    def __get_recipes(self, bs, recipe_category):
        #Devuelve dataframe con la información de las recetas (incluyendo la categoria pasada por parámetro)
        #Dataframe Inicial
        receipes_page = pd.DataFrame(columns=['Id','Categoria','Nombre','Valoracion','Dificultad','NumComensales','Tiempo','Tipo','Descripcion','Link_receta'])
        recipes = bs.findAll("div", {"class": "resultado link", "data-js-selector":"resultado"})
        diff_patern = re.compile(r'Dificultad\s([A-Z,a-z]+)')
        id_pattern = re.compile(r'([0-9]+)\.html')
        for recipe in recipes:
            #Get recipe mandatory features
            recipe_header = recipe.find("a", {"class":"titulo titulo--resultado"})
            recipe_name = recipe_header.getText()
            recipe_id   = id_pattern.search(recipe_header.attrs["href"]).group(1)
            recipe_intro = recipe.find("div", {"class":"intro"}).getText()
            #TODO -> Ampliar intro, la descripcion a veces está partida
            #Get recipe Optional features
            recipe_numPeople = recipe.find("span", {"class":"property comensales"}).getText() if recipe.find("span", {"class":"property comensales"}) else ""
            recipe_time  = recipe.find("span", {"class":"property duracion"}).getText() if recipe.find("span", {"class":"property duracion"}) else ""
            recipe_type = recipe.find("span", {"class":"property para"}).getText() if recipe.find("span", {"class":"property para"}) else ""
            recipe_val   = recipe.find("div", {"class":"valoracion"}).getText() if recipe.find("div", {"class":"valoracion"}) else ""
            recipe_diff = diff_patern.search(recipe.text).group(1) if diff_patern.search(recipe.text) else ""
            recipe_link = recipe_header.attrs["href"]
            #Append to dataframe
            receipes_page = receipes_page.append({'Id':recipe_id,
                                                  'Categoria':recipe_category,
                                                  'Nombre':recipe_name,
                                                  'Valoracion':recipe_val,
                                                  'Dificultad':recipe_diff,
                                                  'NumComensales':recipe_numPeople,
                                                  'Tiempo':recipe_time,
                                                  'Tipo':recipe_type,
                                                  'Descripcion':recipe_intro,
                                                  'Link_receta':recipe_link},ignore_index=True)
        return receipes_page

    def scrape(self):
        #Extrae la información de las recetas y la almacena en memoria
        bs_main = self.__download_html_and_parse(self.url)
        recipes_category_info = self.__get_recipes_category_info(bs_main)
        for recipes_category_info_item in recipes_category_info:
            recipe_category = recipes_category_info_item[0]
            link = recipes_category_info_item[1]
            there_are_more_recipes = True
            while there_are_more_recipes:
                bs_recipes = self.__download_html_and_parse(link)
                recipes = self.__get_recipes(bs_recipes, recipe_category)
                self.data = pd.concat([self.data, recipes], axis=0, sort=False)
                link = self.__get_next_page_link(bs_recipes)
                #if link is None: TODO -> descomentar para recoger todas las paginas!
                there_are_more_recipes = False


    def data2csv(self, filename):
        #Guarda la información de las recetas en un fichero CSV
        #file = open("../csv/" + filename, "w+")
        self.data.to_csv("./../csv/" + filename, index=False, header=True, sep="|")
