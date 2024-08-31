#from Services.DataProcessService import DataProcessService
from Services.DetailFinderService import DetailFinderService
#from ActionProcessor import ActionProcessor
#from Services.SpellcheckerService import SpellcheckerService
#from Services.SearchImagesService import SearchImagesService
#from Services.KerasOCRService import KerasOCRService
from Services.EvaluationService import EvaluationService

#keras_ocr = KerasOCRService()
#text = keras_ocr.read_in_files("C:\\Masterarbeit_ocr_env\\wine_images\\archiv20\\abenheim_liebfrauenmorgen.jpg")
#print(text)
#action = ActionProcessor()
#action.create_entities_for_labels()

#loaded_input_file = preprocessor.load_data('data/english_words.csv')
#print(loaded_input_file)

#data = DataProcessService()

#filepath = "D:\\masterarbeit_saver_all\\enwiki-latest-pages-articles.xml\\enwiki-latest-pages-articles.xml"
#output_file = "dictionary_files/english_extracted_words_750k_uml_en.txt"
#data.create_txt_from_wikimedia(filepath, output_file, 750000, language="en")

#action_processor3 = ActionProcessor()
#action_processor3.correct_sentence_spelling("tesseract", "text_translation_modified_images, tesseract.path",
                                          #  "text_final", use_ml=True)


#action = ActionProcessor()
#action.check_directory_for_duplicates(None)

#search = SearchImagesService()
#search.search_algorithm("riesling aus deutschland", False)
#search.text_based_keyword_search("Zeige mir Riesling und Merlot Weine aus der Region Mosel aus 1900")
#entities = search.named_entity_recognition("Zeige mir Riesling und Merlot Weine aus der Region Mosel von 1900")
#print(entities)

'''
details = DetailFinderService(init_path_text_dict=True)
anno = details.find_anno("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(anno)

vol = details.find_vol("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(vol)
anno = details.find_anno("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(anno)
countries = details.find_country("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(countries)
provinces = details.find_provinces("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(provinces)

wine_types = details.find_wine_type("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(wine_types)
'''
#action = ActionProcessor()

#all_paths_in_db_tupels = action.update_label_detail_infos()

evaluation = EvaluationService()
eval_result_word, summed_eval_score_word = evaluation.do_ocr_eval("word_error_rate_eval", "C:\\Masterarbeit_ocr_env\\Evaluation", "text_final", "doctr")
print(eval_result_word)
print(summed_eval_score_word)

eval_result_char, summed_eval_score_char = evaluation.do_ocr_eval("char_error_rate_eval", "C:\\Masterarbeit_ocr_env\\Evaluation", "text_final", "doctr")
print(eval_result_char)
print(summed_eval_score_char)

eval_result_char, summed_eval_score_char = evaluation.do_ocr_eval("relevant_words_present_eval", "C:\\Masterarbeit_ocr_env\\Evaluation\\archiv19", "text_final", "doctr")
print(eval_result_char)
print(summed_eval_score_char)

