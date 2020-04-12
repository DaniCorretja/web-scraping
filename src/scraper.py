import requests
import pandas as pd
import re
import time
from datetime import date
from bs4 import BeautifulSoup

class RecipesScraper():

    def __init__(self):
        #Inicializa el objecto RecipesScraper
        self.url = "https://www.recetasgratis.net"
        self.columns = ['Id','Categoria','Nombre','Valoracion','Dificultad','Num_comensales','Tiempo','Tipo','Link_receta','Num_comentarios','Num_reviews','Fecha_modificacion','Ingredientes']
        self.data = pd.DataFrame(columns=self.columns)

    def __download_html(self, url):
        #Decarga una página HTML y la devuelve
        #Modificar las cabeceras de la request
        headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Encoding": "gzip, deflate, sdch, br",
                 "Accept-Language": "en-US,en;q=0.8",
                 "Cache-Control": "no-cache", "dnt": "1",
                 "Pragma": "no-cache", "Upgrade-Insecure-Requests": "1",
                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:75.0) Gecko/20100101 Firefox/75.0"}
        responseCode = ""
        timeout = 5
        response = ""
        retries = 0
        #Intentamos hasta 3 veces descargar la pagina
        while responseCode.startswith("2") == False and retries < 3:
            response = requests.get(url, headers=headers, timeout=timeout)
            responseCode = str(response.status_code)
            retries += 1
            timeout = timeout**2

        return response.text

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

    def __get_recipe_ingredients(self, bs_recipe):
        ingredients = []
        labels_ingredients = bs_recipe.find("div", {"class": "ingredientes"}).findAll("label") if bs_recipe.find("div", {"class": "ingredientes"}) else []
        for label in labels_ingredients:
            ingredients.append(label.getText().strip())
        return (',').join(ingredients)

    def __get_recipe_details(self, recipe_link):
        #Devuelve los detalles de una receta.
        #Patterns para regular expressions
        votes_pattern = re.compile(r'([0-9]+)\s\S')
        comment_pattern = re.compile(r'([0-9]+)\s\S')
        date_pattern   = re.compile(r'([0-9]+\s+\S+\s+[0-9]+)')
        #Inicialización de datos
        post_date = None
        recipe_nvotes = 0
        recipe_ncomments = 0
        #Lectura del HTML
        bs_recipe = self.__download_html_and_parse(recipe_link)
        #Extraccion de datos
        basic_data = bs_recipe.find("div", {"class": "daticos"})
        recipe_nvotes = votes_pattern.search(basic_data.find("span", {"class":"votos"}).getText()).group(1) if basic_data.find("span", {"class":"votos"}) else 0
        has_comments = bs_recipe.find("a", {"class":"datico", "href":"#comentarios"})
        if has_comments!= None:
            recipe_ncomments = comment_pattern.search(has_comments.find_next_sibling("a").getText()).group(1) if has_comments.find_next_sibling("a") else 0
        post_info  = bs_recipe.find("div", {"class": "nombre_autor"})
        if post_info != None:
            post_date_text = date_pattern.search(post_info.find("span", {"class":"date_publish"}).getText()).group(1) if post_info.find("span", {"class":"date_publish"}) else ""
            if post_date_text != "":
                post_date = self.__format_date(post_date_text)
            else:
                post_date = None
        recipe_ingredients = self.__get_recipe_ingredients(bs_recipe)
        return post_date,recipe_nvotes,recipe_ncomments,recipe_ingredients

    def __format_date(self, string_date):
        #Formatea la fecha
        months = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}
        date_spit = string_date.lower().strip().split(" ")
        recipe_date = date(int(date_spit[2]), months.get(date_spit[1]), int(date_spit[0]))
        return recipe_date

    def __get_recipes(self, bs, recipe_category):
        #Devuelve dataframe con la información de las recetas (incluyendo la categoria pasada por parámetro)
        #Dataframe Inicial
        receipes_page = pd.DataFrame(columns=self.columns)
        recipes = bs.findAll("div", {"class": "resultado link", "data-js-selector":"resultado"})
        diff_patern = re.compile(r'Dificultad\s(.+)')
        id_pattern = re.compile(r'([0-9]+)\.html')
        val_pattern = re.compile(r'width:\s?(.+)%')

        for recipe in recipes:
            #Get recipe mandatory features
            recipe_header = recipe.find("a", {"class":"titulo titulo--resultado"})
            recipe_name = recipe_header.getText()
            recipe_id   = id_pattern.search(recipe_header.attrs["href"]).group(1)

            #Get recipe Optional features
            recipe_numPeople = recipe.find("span", {"class":"property comensales"}).getText() if recipe.find("span", {"class":"property comensales"}) else ""
            recipe_time  = recipe.find("span", {"class":"property duracion"}).getText() if recipe.find("span", {"class":"property duracion"}) else ""
            recipe_type = recipe.find("span", {"class":"property para"}).getText() if recipe.find("span", {"class":"property para"}) else ""
            recipe_val   = recipe.find("div", {"class":"valoracion"}).attrs["style"] if recipe.find("div", {"class":"valoracion"}) else ""
            mval =  val_pattern.search(recipe_val)
            if mval != None:
                recipe_val = val_pattern.search(recipe_val).group(1) if val_pattern.search(recipe_val) else None
                recipe_val = round(float(recipe_val)/20,1)
            else:
                recipe_val = None
            recipe_diff = diff_patern.search(recipe.text).group(1) if diff_patern.search(recipe.text) else ""
            recipe_link = recipe_header.attrs["href"]
            #Get recipe details
            recipe_date,recipe_nvotes,recipe_ncomments,recipe_ingredients = self.__get_recipe_details(recipe_link)
            #Append to dataframe
            receipes_page = receipes_page.append({'Id':recipe_id,
                                                  'Categoria':recipe_category,
                                                  'Nombre':recipe_name,
                                                  'Valoracion':recipe_val,
                                                  'Dificultad':recipe_diff,
                                                  'Num_comensales':recipe_numPeople,
                                                  'Tiempo':recipe_time,
                                                  'Tipo':recipe_type,
                                                  'Link_receta':recipe_link,
                                                  'Num_comentarios': recipe_ncomments,
                                                  'Num_reviews': recipe_nvotes,
                                                  'Fecha_modificacion': recipe_date,
                                                  'Ingredientes': recipe_ingredients
                                                  },ignore_index=True)
        return receipes_page

    def scrape(self):
        #Extrae la información de las recetas y la almacena en memoria
        #Log inicial
        print("Iniciando el proceso de web scraping para extraer recetas desde " + \
        "'" + self.url + "'...")
        print("Este proceso puede tardar unos 120 minutos.\n")

		#Iniciamos el timer
        start_time = time.time()

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
                if link is None:
                    there_are_more_recipes = False

        #Mostramos el tiempo que ha tardado
        end_time = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
        print ("\nDuración del proceso: ", total_time)

    def data2csv(self, filename):
        #Guarda la información de las recetas en un fichero CSV
        self.data.to_csv("./../csv/" + filename, index=False, header=True, sep="|")
