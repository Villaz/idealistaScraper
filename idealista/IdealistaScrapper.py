from selenium import webdriver
from selenium import common
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from vivienda import Vivienda
from map import Map
from images import Images
from datetime import datetime
import argparse

BASE_URL = 'https://www.idealista.com/'


class IdealistaScrapper:
    """
    Clase encargada de scrapear la página de Idealista
    """

    info = None

    def __init__(self, tipo, location):
        """
        Inicializador de la clase IdealistaScrapper.
        Dentro del método se inicializa la url con el tipo de vivienda y la localizacion donde se
        desea realiizar el scraping.
        En base a estos parámetros se generan los ficheros de salida.
        :param tipo: Tipo de activo a capturar, vivienda, garaje, trastero, etc.
        :param location: Localización donde se desea buscar.
        """
        today = datetime.now().strftime('%Y%m%d')
        self.url = "{0}{1}/{2}/".format(BASE_URL, tipo, location)
        self.file_name = "{0}_{1}_{2}.csv".format(today, tipo, location)
        self.file_images_name = "{0}_{1}_{2}_images.csv".format(today, tipo, location)

    def process(self, deeper: bool=True):
        """
        Función encargada de realizar el scrapeo.
        El parametro deeper indica si se debe de buscar en la página de detalle del activo o unicamente
        se desea capturar la página de listado.
        :param deeper: True si se desea capturar el detalle, false en caso contrario.
        :return: None
        """
        # Se realiza el scraping de las páginas de listado
        self._scrap_list_pages(self.url)
        # Si el parametro de deeper es true buscamos los detalles de cada activo
        if deeper:
            #Generamos un array con todas las entradas capturas, por cada una de ellas
            # capturamos los detalles de la vivienda y las urls de las imágenes.
            # finalmente vamos guardando los datos de manera incremental en el csv correspondiente.
            entries = [Vivienda(i) for i in self.info.to_dict(orient='records')]
            for entry in entries:
                vivienda, images = self.get_detailed_info_from_entry(entry)
                with open(self.file_name, 'a') as f:
                    pd.DataFrame(data=[vivienda.to_dict()]).to_csv(f, header=f.tell() == 0, index=False, mode='a')
                if images is not None:
                    with open(self.file_images_name, 'a') as f:
                        images.to_csv(f, header=f.tell() == 0, index=False, mode='a')
        else:
            self.info.to_csv(self.file_name, header=True, index=False)

    def _scrap_list_pages(self, url: str):
        """
        Realiza el scrapeo de la página de listado.
        :param url: URL sobre la que realizar el scraping.
        :return: None
        """
        driver = webdriver.Firefox()
        driver.get(url)
        driver.implicitly_wait(10)# Por defecto se esperan 10 segundos para cargar los componentes.
        driver.set_page_load_timeout(20)# Si a los 20 segundos no se ha finalizado la larga se produce un timeout

        # Cada activo se encuentra dentro del tag article con class item, encontramos todos los existentes
        # y los recorremos leyendo la informacion que contienen.
        articles = driver.find_elements_by_xpath("//article[contains(@class, 'item')]")
        info = [self._extract_top_information(article) for article in articles]
        info = [i.to_dict() for i in info]
        self.info = pd.DataFrame(data=info) if self.info is None else pd.concat([self.info, pd.DataFrame(data=info)])
        # Buscamos la página en la que nos encontramos, si no existe la clase pagination, o
        # no existe el elemento con clase next es que hemos llegado al final de las páginas.
        # En este caso se lanza una excepción y se finaliza la captura.
        # Con el fin de evitar en cierta medida el banneo por parte del proveedor, cada scrapeo de página
        # se realiza con una instancia diferente del navegador, por ello una vez finalizado se llama a driver.quit()
        try:
            pagination = driver.find_element_by_class_name('pagination')
            url = pagination.find_element_by_class_name('next').find_element_by_tag_name('a').get_attribute('href')
            driver.quit()
            self._scrap_list_pages(url)
        except NoSuchElementException:
            print("Finished")
        finally:
            driver.quit()

    def _extract_top_information(self, article: WebElement) -> Vivienda:
        """
        Extrae la información de cada activo a partir de los datos encontrados en la pagina de listado
        :param article: elemento articulo que se desea scrapear.
        :return:
        """
        info = article.find_element_by_class_name('item-info-container')

        vivienda = Vivienda()
        vivienda.link = info.find_element_by_class_name('item-link').get_attribute('href')
        vivienda.code = vivienda.link.split('/')[-2]
        vivienda.price = info.find_element_by_class_name('item-price').text.replace('€', '').replace('.', '')

        for detail in info.find_elements_by_class_name('item-detail'):
            type_detail = detail.find_element_by_tag_name('small').text
            value = detail.text.replace(type_detail, '').rstrip()
            if type_detail == 'hab.':
                vivienda.rooms = value
            elif type_detail == 'm²':
                vivienda.area = value
            elif 'bajo' in value:
                vivienda.floor = -1
            elif 'planta' in value:
                if value == 'Entreplanta':
                    vivienda.floor = 0.5
                else:
                    vivienda.floor = int(value.replace('ª planta', ''))

            if 'exterior' in detail.text:
                vivienda.exterior = True
            if 'interior' in detail.text:
                vivienda.exterior = False
            if 'con ascensor' in detail.text:
                vivienda.has_elevator = True
            if 'sin ascensor' in detail.text:
                vivienda.has_elevator = False
        return vivienda

    def get_detailed_info_from_entry(self, vivienda: Vivienda):
        """
        Extrae información especifica de cada vivienda a partir de la página de detalle.
        :param vivienda: vivienda sobre la que capturar sus datos ampliados.
        :return: Tupla con primer elemento de vivienda y segundo elemento como un dataframe de imagenes.
        """
        images = None
        # Creamos un nuevo driver para impedir que idealista nos bloquee al pensar que somos un bot.
        driver = webdriver.Firefox()
        try:
            driver.get(vivienda.link)
            driver.implicitly_wait(4)
            driver.set_page_load_timeout(20)
            ubication = driver.find_element_by_id('mapWrapper')
            ubication_data = [i.text for i in ubication.find_elements_by_tag_name('li')]
            vivienda.address = ubication_data[0]
            vivienda.barrio = ubication_data[1]
            vivienda.distrito = ubication_data[2]
            vivienda.ciudad = ubication_data[3]
            vivienda.lat, vivienda.lon = Map(driver).get_lat_lon()
            images = Images(driver, vivienda.code).get_images()
        except common.exceptions.WebDriverException as ex:
            print(ex)
            print(vivienda.link)
            return None, images
        finally:
            driver.quit()
            return vivienda, images


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrapeo idealista')
    parser.add_argument('transaccion', help="Tipo de transaccion a buscar", choices=['venta', 'alquiler'])
    parser.add_argument('tipologia', help='Tipologia a buscar', choices=['viviendas'])
    parser.add_argument('--zona', help='Zona a buscar', default='oviedo-asturias')
    parser.add_argument('--full', help='Busqueda superficial o detalle', default=True)
    args = parser.parse_args()
    i = IdealistaScrapper('{0}-{1}'.format(args.transaccion, args.tipologia), args.zona)
    i.process(args.full)
