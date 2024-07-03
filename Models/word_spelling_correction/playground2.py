
from Models.word_spelling_correction.PreProcessor import PreProcessor


pre_processor = PreProcessor()

input_file = "data/german_words.csv"
loaded_input_file = pre_processor.form_dataframe_german(input_file)

print(loaded_input_file)

