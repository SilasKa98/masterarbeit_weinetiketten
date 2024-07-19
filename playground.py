from Services.DataProcessService import DataProcessService
from Services.DetailFinderService import DetailFinderService
from ActionProcessor import ActionProcessor
from Services.SpellcheckerService import SpellcheckerService


#loaded_input_file = preprocessor.load_data('data/english_words.csv')
#print(loaded_input_file)

data = DataProcessService()

filepath = "D:\\masterarbeit_saver_all\\enwiki-latest-pages-articles.xml\\enwiki-latest-pages-articles.xml"
output_file = "dictionary_files/english_extracted_words_750k_uml_en.txt"
data.create_txt_from_wikimedia(filepath, output_file, 750000, language="en")


'''
details = DetailFinderService()
vol = details.find_vol("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(vol)
anno = details.find_anno("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(anno)
countries = details.find_country("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(countries)
provinces = details.find_provinces("wine_images\\archiv20a\\merl_koenigslay_terrassen.jpg")
print(provinces)
'''
#action = ActionProcessor()

#all_paths_in_db_tupels = action.update_label_detail_infos()

