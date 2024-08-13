import re
import pycountry
from Services.DatabaseService import DatabaseService
from Services.DataProcessService import DataProcessService
from collections import Counter
from collections import defaultdict
from countryinfo import CountryInfo


class DetailFinderService:

    def __init__(self, init_path_text_dict=True):
        self.database_service = DatabaseService()
        if init_path_text_dict:
            self.country_provinces_dict = self.get_provinces()
            self.country_info_dict = self.get_all_countries_with_infos()
            self.path_text_dict = self.fetch_all_texts()
        else:
            self.country_provinces_dict = None
            self.country_info_dict = None
            self.path_text_dict = None

    def fetch_all_texts(self, used_ocrs=["doctr", "easyocr", "tesseract"]):

        db_results_all = []
        for ocr in used_ocrs:
            db_result = self.database_service.select_from_table(ocr, "*", as_dict=True)
            db_results_all.extend(db_result)  # direkt in eine Liste einfügen

        path_text_dict = defaultdict(str)
        for item in db_results_all:
            current_path = item.pop("path", None)
            if current_path:
                path_text_dict[current_path] += " " + " ".join(item.values())

        return dict(path_text_dict)

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

    def find_wine_type(self, path):
        text = self.path_text_dict[path]
        with open(f"C:\\Masterarbeit_ocr_env\\dictionary_files\\red_wine_names.txt", "r", encoding="utf-8") as file:
            red_wine_names = [item.strip().lower() for item in file]
        with open(f"C:\\Masterarbeit_ocr_env\\dictionary_files\\white_wine_names.txt", "r", encoding="utf-8") as file:
            white_wine_names = [item.strip().lower() for item in file]
        data = DataProcessService()
        is_red_wine = False
        for red_wine in red_wine_names:
            if data.find_text_intersections(red_wine.lower(), text.lower()):
                is_red_wine = True
                break
        is_white_wine = False
        for white_wine in white_wine_names:
            if data.find_text_intersections(white_wine.lower(), text.lower()):
                is_white_wine = True
                break

        if is_red_wine and is_white_wine:
            return "unclear"
        elif is_white_wine:
            return "white wine"
        elif is_red_wine:
            return "red wine"
        else:
            return ""
