
from ActionProcessor import ActionProcessor
from Services.DeepLService import DeepLService
from Services.DataProcessService import DataProcessService
from Services.SearchImagesService import SearchImagesService
from Services.MachineLearningService import MachineLearningService
from Models.word_spelling_correction.PreProcessor import PreProcessor



#search_text = "Riesling und Lemberger Qualitätswein"
#searchImage = SearchImagesService()
#search_result = searchImage.search(search_text, True)
#print(search_result)


def main():
    # action_processor = ActionProcessor()
    # action_processor.search_for_duplicate_entrys('easyocr', 'text_translation', save='True', save_table='duplicates')

    #machine_learning = MachineLearningService('german_words', '256Dim_512Batch_adam_german')
    #pre_processor = PreProcessor()
    #machine_learning.ml_word_correction('speicherplasz', 256, pre_processor.form_dataframe_german)

    action_processor = ActionProcessor()
    action_processor.correct_sentence_spelling("easyocr", "text_translation, easyocr.path", "text_translation_spellchecker", use_ml=False, lang_filter="de")

    # action_processor = ActionProcessor()
    # action_processor.modify_images("wine_images")

    # read in image texts--> can set lang detection True/False to read texts with expected lang
    #action_processor = ActionProcessor()
    #action_processor.read_and_save_ocr("tesseract", "wine_images/", "tesseract",
                                      # "modified_images", use_translation=True, only_new_entrys=False)

    # detect language with db entrys
    # action_processor.read_db_and_detect_lang()


if __name__ == "__main__":
    main()

