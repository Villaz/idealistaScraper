from selenium import webdriver
from selenium import common
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from idealista.vivienda import Vivienda
from idealista.map import Map
from idealista.images import Images
from datetime import datetime

BASE_URL = 'https://www.idealista.com/'


class IdealistaScrapper:

    info = None

    def __init__(self, tipo, location):
        today = datetime.now().strftime('%Y%m%d')
        self.url = "{0}{1}/{2}/".format(BASE_URL, tipo, location)
        self.file_name = "{0}_{1}_{2}.csv".format(today, tipo, location)
        self.file_images_name = "{0}_{1}_{2}_images.csv".format(today, tipo, location)

    def process(self, deeper=True):
        self._scrap(self.url)
        if deeper:
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

    def _scrap(self, url):
        driver = webdriver.Firefox()
        driver.get(url)
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(20)

        articles = driver.find_elements_by_xpath("//article[contains(@class, 'item')]")
        info = [self._extract_top_information(article) for article in articles]
        info = [i.to_dict() for i in info]
        self.info = pd.DataFrame(data=info) if self.info is None else pd.concat([self.info, pd.DataFrame(data=info)])
        try:
            pagination = driver.find_element_by_class_name('pagination')
            url = pagination.find_element_by_class_name('next').find_element_by_tag_name('a').get_attribute('href')
            driver.quit()
            #self._scrap(url)
        except NoSuchElementException:
            print("Finished")
        finally:
            driver.quit()

    def _extract_top_information(self, article: WebElement):
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

    def get_detailed_info_from_entry(self, vivienda):
        images = None
        #Creamos un nuevo driver para impedir que idealista nos bloquee al pensar que somos un bot.
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




i = IdealistaScrapper('venta-viviendas', 'oviedo-asturias')
i.process(True)