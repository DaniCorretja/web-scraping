import requests
import pandas as pd
from bs import BeautifulSoup

class RecipesScraper():

    def __init__(self):
        #Inicializa el objecto RecipesScraper
        self.url = "https://www.recetasgratis.net"
        self.data = pd.DataFrame(columns=['Id','Categoria','Nombre','Valoracion','Dificultad','NumComensales','Tiempo','Tipo','Descripcion'])

    def __download_html(self, url):
        #Decarga una página HTML y la devuelve
        return requests.get(url).text

    def __download_html_and_parse(self, url):
        #Decarga una página HTML, la parsea, y la devuelve
		return BeautifulSoup(self.__download_html(url).text, 'html.parser')

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
        a_next_page = paginator.find("span", {"class":"current"}).find_next_sibling("a")
        if (a_next_page is not None):
            return a_next_page.attrs["href"]
        return None

    def __get_recipes(self, bs, recipe_category):
        #Devuelve dataframe con la información de las recetas (incluyendo la categoria pasada por parámetro)
        #Dataframe Inicial
        receipes_page = pd.DataFrame(columns=['Id','Categoria','Nombre','Valoracion','Dificultad','NumComensales','Tiempo','Tipo','Descripcion'])
        recipes = bs.findAll("div", {"class": "resultado link", "data-js-selector":"resultado"})
        diff_patern = re.compile(r'Dificultad\s([A-Z,a-z]+)')
        id_pattern = re.compile(r'([0-9]+)\.html')
        for recipe in recipes:
            #Get recipe mandatory features
            recepie_header = recipe.find("a", {"class":"titulo titulo--resultado"})
            recepie_name = recepie_header.getText()
            recepie_id   = id_pattern.search(recepie_header.attrs["href"]).group(1)
            recepie_intro = recipe.find("div", {"class":"intro"}).getText()
            #TODO -> Ampliar intro, la descripcion a veces está partida
            #Get recipe Optional features
            recepie_numPeople = recipe.find("span", {"class":"property comensales"}).getText() if recipe.find("span", {"class":"property comensales"}) else ""
            recepie_time  = recipe.find("span", {"class":"property duracion"}).getText() if recipe.find("span", {"class":"property duracion"}) else ""
            recepie_type = recipe.find("span", {"class":"property para"}).getText() if recipe.find("span", {"class":"property para"}) else ""
            recepie_val   = recipe.find("div", {"class":"valoracion"}).getText() if recipe.find("div", {"class":"valoracion"}) else ""
            recepie_diff = diff_patern.search(recipe.text).group(1) if diff_patern.search(recipe.text) else ""
            #Append to dataframe
            receipes_page = receipes_page.append({'Id':recepie_id,
                                                  'Categoria':recipe_category,
                                                  'Nombre':recepie_name,
                                                  'Valoracion':recepie_val,
                                                  'Dificultad':recepie_diff,
                                                  'NumComensales':recepie_numPeople,
                                                  'Tiempo':recepie_time,
                                                  'Tipo':recepie_type,
                                                  'Descripcion':recepie_intro},ignore_index=True)
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
                self.data.append(recipes)
                link = self.__get_next_page_link(bs_recipes)
                if link is None:
                    there_are_more_recipes = False


    def data2csv(self, filename):
        #Guarda la información de las recetas en un fichero CSV
		file = open("../csv/" + filename, "w+")
        df.to_csv("..\csv" + filename, index=False, header=True)
