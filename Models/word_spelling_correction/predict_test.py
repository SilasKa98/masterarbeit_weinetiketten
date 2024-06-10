import numpy as np

from Models.word_spelling_correction.ModelPreparation import ModelPreparation
from Models.word_spelling_correction.PreProcessor import PreProcessor
import tensorflow as tf


preprocessor = PreProcessor()
model_prep = ModelPreparation()

all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzüöä0123456789")
char_indexing = preprocessor.char_indexing(all_existing_chars)
int_char_dict = char_indexing[0]
char_int_dict = char_indexing[1]


input_file = "data/german_words.csv"
loaded_input_file =preprocessor.form_dataframe_german(input_file)

print(loaded_input_file)

string_lines = preprocessor.count_lines(loaded_input_file)

#string_lines = preprocessor.word_splitting(string_lines)

cleaned_string_lines = []
for cleaned_str in string_lines:
    cln = preprocessor.word_cleaning(cleaned_str)
    cleaned_string_lines.append(cln)

string_lines = cleaned_string_lines

training_data = model_prep.create_training_data(string_lines)

input_vals = training_data[0]
target_vals = training_data[1]
encoded_max_length = training_data[2]
decoded_max_length = training_data[3]





#loaded_model = tf.keras.models.load_model('savedModels/new_test_model_2.h5',
                                        #  custom_objects=None,
                                         # compile=True,
                                         # safe_mode=True
                                        #  )

#corrected_word = model_prep.make_correction("tabener", loaded_model, char_int_dict, int_char_dict)
#print("Corrected Word:", corrected_word)
print(target_vals)

test_text = "wurttemberg"

input_token_index = dict([(char, i) for i, char in enumerate(char_int_dict)])

print("encMaxLen ",encoded_max_length)
print("allExCharsLen ",len(all_existing_chars))

encoder_test_data = np.zeros((1, encoded_max_length, len(all_existing_chars)), dtype='float32')

for t, char in enumerate(test_text):
    print(input_token_index)
    print(input_token_index[char])
    encoder_test_data[0, t, input_token_index[char]] = 1.0

#decoded_sentence = model_prep.decode_sequence(encoder_test_data)
decoded_sentence = model_prep.doPredict(encoder_test_data, "savedModels/256Dim_512Batch_adam_german.h5",256, char_int_dict, all_existing_chars, decoded_max_length)
print("Input: ",test_text,"\n")
print("Output: ",decoded_sentence,"\n")

