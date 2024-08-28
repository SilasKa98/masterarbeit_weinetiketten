import time
from Services.SearchImagesService import SearchImagesService
from Services.DatabaseService import DatabaseService

class EvaluationService:

    def __init__(self):
        print("init EvalService")

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
