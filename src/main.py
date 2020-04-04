from scraper import RecipesScraper

output_file = "recetas.csv";

scraper = RecipesScraper();
scraper.scrape();
scraper.data2csv(output_file);