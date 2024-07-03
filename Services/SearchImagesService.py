from Services.DataProcessService import DataProcessService
from ActionProcessor import ActionProcessor
from Services.DatabaseService import DatabaseService


class SearchImagesService:

    def __init__(self):
        self.database_service = DatabaseService()

    def search_normal(self, search_text, used_ocrs=["easyocr", "tesseract", "doctr"]):
        search_text_keywords = DataProcessService.create_keywords_of_scentence(search_text, "de", 4, 6, 0.9)

        print(search_text_keywords)

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

        intersection_dict = {}
        for key, text in path_text_dict.items():
            for keyword in search_text_keywords:
                text_intersection = DataProcessService.find_text_intersections(keyword[0], text)
                if text_intersection is not None:
                    text_intersection_str = next(iter(text_intersection))
                    if text_intersection_str in intersection_dict:
                        intersection_dict[text_intersection_str].add(key)
                    else:
                        intersection_dict[text_intersection_str] = {key}

        return intersection_dict

