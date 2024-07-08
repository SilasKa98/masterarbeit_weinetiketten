from Services.DataProcessService import DataProcessService
from Services.DetailFinderService import DetailFinderService
from ActionProcessor import ActionProcessor

data = DataProcessService()
#loaded_input_file = preprocessor.load_data('data/english_words.csv')
#print(loaded_input_file)
'''
filepath = "C:\\Users\\Silas-Pc\\Downloads\\dewiki-latest-pages-articles\\dewiki-latest-pages-articles.xml"
output_file = "dictionary_files/german_extracted_words_20mio_uml.txt"
data.create_txt_from_wikimedia(filepath, output_file, 20000000)
'''

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
action = ActionProcessor()

all_paths_in_db_tupels = action.update_label_detail_infos()

