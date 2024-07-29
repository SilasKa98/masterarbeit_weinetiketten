from Models.word_spelling_correction.PreProcessor import PreProcessor
from Models.word_spelling_correction.ModelPreparation import ModelPreparation


preprocessor = PreProcessor()
#loaded_input_file = preprocessor.load_data('data/english_words.csv')
#print(loaded_input_file)

input_file = "data/french_extracted_words_750k_uml_fr.txt"
loaded_input_file = preprocessor.form_dataframe_german_txt(input_file)
word_cleaning_lang = "fr"
print(loaded_input_file)

# german
# all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzüöä0123456789-")

# english
#all_existing_chars = list(" abcdefghijklmnopqrstuvwxyz0123456789-")

# italian
#all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzàèéìòù0123456789-")

# french
all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzàâæçèéêëîïôœùûüÿ0123456789-")


string_lines = preprocessor.count_lines(loaded_input_file)

#string_lines = preprocessor.word_splitting(string_lines)
cleaned_string_lines = []
for cleaned_str in string_lines:
    cln = preprocessor.word_cleaning(cleaned_str, lang=word_cleaning_lang)
    cleaned_string_lines.append(cln)

string_lines = cleaned_string_lines

print(string_lines[:20])
char_indexing = preprocessor.char_indexing(all_existing_chars)
int_char_dict = char_indexing[0]
char_int_dict = char_indexing[1]

model_preparation = ModelPreparation()
training_data = model_preparation.create_training_data(string_lines, all_existing_chars, german=False)

input_vals = training_data[0]
target_vals = training_data[1]
encode_max_length = training_data[2]
decoded_max_length = training_data[3]

zero_vectors = model_preparation.create_zero_vectors(input_vals, encode_max_length, decoded_max_length, all_existing_chars)

encoder_input_data = zero_vectors[0]
decoder_input_data = zero_vectors[1]
decoder_target_data = zero_vectors[2]

one_hots = model_preparation.fill_data_arrays(input_vals, target_vals, encoder_input_data, decoder_input_data, decoder_target_data, char_int_dict)

#one_hots = model_preparation.fill_data_arrays_2(input_vals, target_vals, encoder_input_data, decoder_input_data, decoder_target_data, char_int_dict)

encoder_input_data = one_hots[0]
decoder_input_data = one_hots[1]
decoder_target_data = one_hots[2]

#model_preparation.create_ml_model_2(256, 2000, 256, all_existing_chars, encoder_input_data, decoder_input_data, decoder_target_data)

model_preparation.create_ml_model(96, 18, 312, all_existing_chars, encoder_input_data, decoder_input_data, decoder_target_data)

#model_preparation.create_ml_model_with_tuning(128, 100, all_existing_chars, encoder_input_data, decoder_input_data, decoder_target_data)