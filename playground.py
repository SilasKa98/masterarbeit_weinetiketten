from Models.word_spelling_correction.ModelPreparation import ModelPreparation

preprocessor = ModelPreparation()
#loaded_input_file = preprocessor.load_data('data/english_words.csv')
#print(loaded_input_file)

preprocessor.create_training_data()


