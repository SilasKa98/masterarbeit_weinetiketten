import re

import pycountry
from Services.DatabaseService import DatabaseService
from collections import Counter
from countryinfo import CountryInfo


class DetailFinderService:

    def __init__(self):
        self.database_service = DatabaseService()
        self.country_provinces_dict = self.get_provinces()
        self.country_info_dict = self.get_all_countries_with_infos()
        self.path_text_dict = self.fetch_all_texts()

    def fetch_all_texts(self, used_ocrs=["doctr", "easyocr", "tesseract"]):

        db_results_all = []
        for ocr in used_ocrs:
            db_result = self.database_service.select_from_table(ocr, "*", as_dict=True)
            db_results_all.append(db_result)

        path_text_dict = {}
        for inner_list in db_results_all:
            for item in inner_list:
                for key, value in item.items():
                    if key == "path":
                        current_path = value
                    else:
                        if current_path in path_text_dict:
                            path_text_dict[current_path] = path_text_dict[current_path] + " " + value
                        else:
                            path_text_dict[current_path] = value

        return path_text_dict

    def find_anno(self, path):
        text = self.path_text_dict[path]
        # etiketten jahreszahlen von 1400 bis 2099
        pattern = r'\b(14\d{2}|15\d{2}|16\d{2}|17\d{2}|18\d{2}|19\d{2}|20\d{2})\b'
        anno_list = re.findall(pattern, text)
        counter = Counter(anno_list)
        if counter:
            most_common_element = counter.most_common(1)[0][0]
        else:
            most_common_element = None
        return most_common_element

    def find_vol(self, path):
        text = self.path_text_dict[path]
        pattern = r'\b\d{1,2}[.,]\d{1,2}%\s*vol|\b\d{1,2}%\s*vol|\b\d{1,2}[.,]\d{1,2}%|\b\d{1,2}%'
        vol_list = re.findall(pattern, text)
        # Clean up the results by removing any "vol" and trailing spaces
        #vol_list = [re.sub(r'\s*vol', '', v).strip() for v in vol_list]
        counter = Counter(vol_list)
        if counter:
            most_common_element = counter.most_common(1)[0][0].replace("vol","");
        else:
            most_common_element = None
        return most_common_element

    @staticmethod
    def get_provinces():
        country_provinces_dict = {}
        all_countries = pycountry.countries
        for item in all_countries:
            country_infos = CountryInfo(item.name)
            try:
                country_provinces = country_infos.provinces()
            except KeyError:
                pass
            country_provinces_dict[item.name] = []
            country_provinces_dict[item.name] += list(set([x for x in country_provinces if len(x) > 2]))
        return country_provinces_dict

    def find_provinces(self, path):
        text = self.path_text_dict[path]
        found_province = list(set())
        for key, values in self.country_provinces_dict.items():
            for item in values:
                if re.search(rf"\b{re.escape(item)}\b", text, flags=re.IGNORECASE):
                    found_province.append(item)

        return found_province

    @staticmethod
    def get_all_countries_with_infos():
        all_countries = pycountry.countries
        country_info_dict = {}
        for item in all_countries:
            country_infos = CountryInfo(item.name)
            try:
                country_provinces = country_infos.provinces()
                country_alt_spelling = country_infos.alt_spellings()
                country_capital = country_infos.capital()
                country_region = country_infos.region()
                country_translations = country_infos.translations()
            except KeyError:
                pass
            country_info_dict[item.name] = []
            country_info_dict[item.name].append(item.name)
            country_info_dict[item.name] += list(set([x for x in country_provinces if len(x) > 2]))
            country_info_dict[item.name] += list(set([x for x in country_alt_spelling if len(x) > 2]))
            country_info_dict[item.name] += list(set([value for key, value in country_translations.items() if key != 'ja' and len(value) > 2]))
            country_info_dict[item.name].append(country_capital)
            country_info_dict[item.name].append(country_region)

        return country_info_dict

    def find_country(self, path):
        text = self.path_text_dict[path]
        found_countries = list(set())
        for key, values in self.country_info_dict.items():
            for item in values:
                if re.search(rf"\b{re.escape(item)}\b", text, flags=re.IGNORECASE) and item != "" and item is not None:
                    found_countries.append(key)
        return found_countries
