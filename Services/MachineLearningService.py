import numpy as np
import os

from Models.word_spelling_correction.ModelPreparation import ModelPreparation
from Models.word_spelling_correction.PreProcessor import PreProcessor


class MachineLearningService:

    def __init__(self, data_file, model_name):
        self.current_path = os.getcwd()
        self.input_file = os.path.join(self.current_path, f'C:/Masterarbeit_ocr_env/Models/word_spelling_correction/data/{data_file}')
        self.model_to_use = os.path.join(self.current_path, f'C:/Masterarbeit_ocr_env/Models/word_spelling_correction/savedModels/{model_name}')

    def ml_word_correction_init(self, dataframe_function, language="en"):

        preprocessor = PreProcessor()
        model_prep = ModelPreparation()

        if language == "de":
            all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzüöäß0123456789-")
            use_german = True
        elif language == "fr":
            all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzàâæçèéêëîïôœùûüÿ0123456789-")
            use_german = False
        elif language == "it":
            all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzàèéìòù0123456789-")
            use_german = False
        elif language == "en":
            all_existing_chars = list(" abcdefghijklmnopqrstuvwxyz0123456789-")
            use_german = False
        char_indexing = preprocessor.char_indexing(all_existing_chars)
        int_char_dict = char_indexing[0]
        char_int_dict = char_indexing[1]

        input_file = self.input_file
        loaded_input_file = dataframe_function(input_file)

        string_lines = preprocessor.count_lines(loaded_input_file)

        cleaned_string_lines = []
        for cleaned_str in string_lines:
            cln = preprocessor.word_cleaning(cleaned_str, lang=language)
            cleaned_string_lines.append(cln)

        string_lines = cleaned_string_lines

        training_data = model_prep.create_training_data(string_lines, all_existing_chars, german=use_german)

        input_vals = training_data[0]
        target_vals = training_data[1]
        encoded_max_length = training_data[2]
        decoded_max_length = training_data[3]

        return char_int_dict, encoded_max_length, all_existing_chars, decoded_max_length

    def ml_word_correction_exec(self, text_to_predict, dim_size, char_int_dict, encoded_max_length, all_existing_chars, decoded_max_length):
        test_text = text_to_predict

        input_token_index = dict([(char, i) for i, char in enumerate(char_int_dict)])

        encoder_test_data = np.zeros((1, encoded_max_length, len(all_existing_chars)), dtype='float32')

        for t, char in enumerate(test_text):
            if char in input_token_index:
                encoder_test_data[0, t, input_token_index[char]] = 1.0
            else:
                print(f"Character '{char}' not in training set, skipping.")

        # decoded_sentence = model_prep.decode_sequence(encoder_test_data)
        model_prep = ModelPreparation()
        decoded_word = model_prep.doPredict(encoder_test_data, self.model_to_use , dim_size,
                                            char_int_dict, all_existing_chars, decoded_max_length)
        print("Input: ", test_text, "\n")
        print("Output: ", decoded_word, "\n")
        return decoded_word

