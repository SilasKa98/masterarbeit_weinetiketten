from Services.DataProcessService import DataProcessService
from ActionProcessor import ActionProcessor


class SearchImagesService:

    @staticmethod
    def search(search_text, use_translation):
        search_text_keywords = DataProcessService.create_keywords_of_scentence(search_text, "de", 4, 6, 0.9)

        print(search_text_keywords)

        search_in_directory = ActionProcessor()
        directory_results = search_in_directory.process_directory("wine_images/archiv20a", use_translation)
        all_matches = []
        for image in directory_results:
            for keyword in search_text_keywords:
                text_intersection = DataProcessService.find_text_intersections(keyword[0], image[0], image[1])
                if text_intersection is not None:
                    all_matches.append([text_intersection])
        return all_matches

