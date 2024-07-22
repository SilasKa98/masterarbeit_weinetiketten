import deepl
from iso639 import Lang
import langid
from langid.langid import LanguageIdentifier, model
from Services.DataProcessService import DataProcessService
from Services.DatabaseService import DatabaseService

class DeepLService:

    def __init__(self):
        #include with .env file later
        auth_key = "91de05aa-d746-6ef2-3b96-0151d03ca5bf:fx"
        self.translator = deepl.Translator(auth_key)

    @staticmethod
    def deepl_to_iso639_2(deepl_code):

        try:
            iso_lang = Lang(deepl_code.lower())
            return iso_lang.pt2t
        except KeyError:
            return "eng"

    @staticmethod
    def deepl_to_iso639_1(deepl_code):
        try:
            iso_lang = Lang(deepl_code.lower())
            return iso_lang.pt1
        except KeyError:
            return "en"

    @staticmethod
    def detect_language_on_the_fly(input_text):
        identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        identifier.set_languages(['de', 'fr', 'it', 'en'])
        return identifier.classify(input_text)


    def detect_language(self, input_text, image_name, image_directory_name, force_update=False):

        #use keywords of the full context to detect the language to not use too many words for deepl (500k/month free)
        keyword_search = DataProcessService.create_keywords_of_scentence(input_text, "en", 1, 6, 0.9)

        #get keyword text. If its not formed by create_keywords_of_scentence, it will be picking middle 5 words of text
        if len(keyword_search) > 0:
            keyword_text = keyword_search[0][0]
        else:
            text_splitted = input_text.split()
            num_words = len(text_splitted)
            if num_words <= 5:
                keyword_text = ' '.join(text_splitted)
            else:
                middle_index = num_words // 2
                start_index = max(0, middle_index - 2)
                end_index = min(num_words, start_index + 5)
                keyword_text = ' '.join(text_splitted[start_index:end_index])

        try:
            #first search in db for the specific image if there already is a translation
            database_service = DatabaseService()
            database_entry = database_service.select_from_table(
                "etiketten_infos",
                "detected_language",
                "name=%s and image_directory=%s",
                [image_name,image_directory_name]
            )
            found_language_in_db = database_entry[0][0]
            if found_language_in_db == "N/A" or found_language_in_db == "unknown" or found_language_in_db == "" or found_language_in_db is None or force_update is True:
                result = self.translator.translate_text(keyword_text, target_lang="EN-GB")
                deepl_detection = result.detected_source_lang
                return deepl_detection
            else:
                return found_language_in_db
        except IndexError:
            return "eng"

