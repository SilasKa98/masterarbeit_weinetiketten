import difflib
import os
import pprint
import time

import jiwer
from jiwer import wer, cer
import numpy as np

from Services.SearchImagesService import SearchImagesService
from Services.DatabaseService import DatabaseService
from Services.DataProcessService import DataProcessService


class EvaluationService:

    def __init__(self):
        print("init EvalService")
        self.transforms = jiwer.Compose(
            [
                jiwer.ExpandCommonEnglishContractions(),
                jiwer.RemoveEmptyStrings(),
                jiwer.ToLowerCase(),
                jiwer.RemoveMultipleSpaces(),
                jiwer.Strip(),
                jiwer.RemovePunctuation(),
                jiwer.ReduceToListOfListOfWords(),
            ]
        )

    @staticmethod
    def eval_search_time(search_text, search_logic_combined, percentage_matching_range, number_of_used_db_entries):
        database = DatabaseService()
        total_db_entries = database.select_from_table("etiketten_infos", "count(path)")
        calculated_number_of_used_entries = round(int(total_db_entries[0][0]) * (int(number_of_used_db_entries)/100))
        print("calculated_number_of_used_entries", calculated_number_of_used_entries)

        print("start eval search_time")
        start = time.time()
        search = SearchImagesService()
        search.search_algorithm(search_text, search_logic_combined, percentage_matching_range, calculated_number_of_used_entries)
        end = time.time()
        print("execution time: ", end - start)
        processed_end_time = round(end - start, 2)
        return_string = "Die Suchanfrage für \"" + search_text + "\" dauerte " +\
                        str(processed_end_time) + " s. Die zusammenhängende Betrachtung war: " +\
                        str(search_logic_combined) + ". Insgesamt wurden " + str(calculated_number_of_used_entries) +\
                        " Weinetiketten in die Suche einbezogen."
        return_val = [return_string]
        return return_val

    def do_ocr_eval(self, method_to_eval, read_in_directory, used_column, used_ocr="doctr"):
        eval_path_text_dict = {}
        for root, dirs, files in os.walk(read_in_directory):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    file_name_without_extension = os.path.splitext(file)[0]
                    folder_name = os.path.basename(root)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        eval_path_text_dict[f"wine_images\\{folder_name}\\{file_name_without_extension}"] = content

        database = DatabaseService()
        data_processing = DataProcessService()
        eval_result = {}
        for path_key, eval_text in eval_path_text_dict.items():
            escaped_path_key = path_key.replace("\\", "\\\\") + "%"
            print(escaped_path_key)
            db_select = database.select_from_table(used_ocr, f"path, {used_column}", condition="path like %s", params=[escaped_path_key], as_dict=True)
            if db_select:
                ocr_text = db_select[0][used_column]
                ocr_text = data_processing.remove_non_year_numbers(ocr_text)
                ocr_text = data_processing.remove_line_breaks(ocr_text)
                eval_text = data_processing.remove_non_year_numbers(eval_text)
                eval_text = data_processing.remove_line_breaks(eval_text)
                if method_to_eval == "char_error_rate_eval":
                    result = self.char_error_rate_eval(eval_text, ocr_text)
                    eval_result[db_select[0]["path"]] = result
                elif method_to_eval == "word_error_rate_eval":
                    result = self.word_error_rate_eval(eval_text, ocr_text)
                    eval_result[db_select[0]["path"]] = result
        print(eval_result)
        summed_eval_score = round(sum(eval_result.values())/len(eval_result.values()), 2)
        return eval_result, summed_eval_score

    def word_error_rate_eval(self, eval_text, ocr_text):
        print("used word error rate!")
        word_error_rate = wer(
            eval_text,
            ocr_text,
            truth_transform=self.transforms,
            hypothesis_transform=self.transforms
        )
        word_error_rate = round(word_error_rate, 2)
        if word_error_rate > 1:
            word_error_rate = 1
        return word_error_rate

    def char_error_rate_eval(self, eval_text, ocr_text):
        print("used char error rate!")
        char_error_rate = cer(
            eval_text,
            ocr_text,
            truth_transform=self.transforms,
            hypothesis_transform=self.transforms
        )
        char_error_rate = round(char_error_rate, 2)
        if char_error_rate > 1:
            char_error_rate = 1
        return char_error_rate



