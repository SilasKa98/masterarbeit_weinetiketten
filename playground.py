from Services.DataProcessService import DataProcessService

data = DataProcessService()
#loaded_input_file = preprocessor.load_data('data/english_words.csv')
#print(loaded_input_file)

filepath = "C:\\Users\\Silas-Pc\\Downloads\\dewiki-latest-pages-articles\\dewiki-latest-pages-articles.xml"
output_file = "dictionary_files/german_extracted_words_20mio_uml.txt"
data.create_txt_from_wikimedia(filepath, output_file, 20000000)


