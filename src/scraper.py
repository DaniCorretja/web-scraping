import requests
import pandas as pd
from bs4 import BeautifulSoup

class RecipesScraper():

    def __init__(self):
        #Inicializa el objecto RecipesScraper
        self.url = "https://www.recetasgratis.net"
        self.data = pd.DataFrame(columns=['Id','Categoria','Nombre','Valoracion','Dificultad','NumComensales','Tiempo','Tipo','Descripcion'])


    def __download_html(self, url):
        #Decarga una página HTML y la guarda en memoria
		return requests.get(url).text


    def __get_recipes_category_info(self, bs):
        #Devuelve lista de tuples [(nombre_cat1, link1), (nombre_cat2, link2)]
        #TODO

    def __get_next_page_link(self, bs):
        #Devuelve string con la url a la siguiente pagina. En caso de no existir devuelve None
        #TODO

    def __get_recipes(self, bs, recipe_category):
        #Devuelve dataframe con la información de las recetas (incluyendo la categoria pasada por parámetro)
        #TODO

    def scrape(self):
        #Extrae la información de las recetas y la almacena en memoria
        html_main = self.__download_html(self.url)
        bs_main = BeautifulSoup(html_main, 'html.parser')
        recipes_category_info = self.__get_recipes_category_info(bs_main)
        for recipes_category_info_item in recipes_category_info:
            recipe_category = recipes_category_info_item[0]
            link = recipes_category_info_item[1]
            there_are_more_recipes = True
            while there_are_more_recipes:
                html_recipes = self.__download_html(link)
                bs_recipes = BeautifulSoup(html_recipes, 'html.parser')
                recipes = __get_recipes(bs_recipes, recipe_category)
                self.data.append(recipes)
                link = __get_next_page_link(bs_recipes)
                if link is None:
                    there_are_more_recipes = False


    def data2csv(self, filename):
        #Guarda la información de las recetas en un fichero CSV
		file = open("../csv/" + filename, "w+")
        df.to_csv("..\csv" + filename, index=False, header=True)