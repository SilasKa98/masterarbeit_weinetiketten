from matplotlib import pyplot as plt

from Models.word_spelling_correction.PreProcessor import PreProcessor
import numpy as np
from keras.models import Model
from keras.layers import Input, LSTM, Dense
from keras.optimizers import RMSprop
import tensorflow as tf
from keras.models import load_model
from keras.callbacks import EarlyStopping
from keras.callbacks import ReduceLROnPlateau
from keras.layers import Dropout
from kerastuner.tuners import RandomSearch

class ModelPreparation:

    def __init__(self):
        self.pre_processor = PreProcessor()

    # create a dataset for training
    def create_training_data(self, string_lines, all_existing_chars, german=False):
        print("string_lines ", len(string_lines))
        input_vals = []
        target_vals = []
        start_factor = 0.75
        start_point = int(len(string_lines)*start_factor)
        #start_point = 0
        repeats = 3

        for str_val in string_lines[start_point:]:
            if len(str_val) > 5:
                target_val = '\t' + str_val + '\n'
                for _ in range(repeats):
                    input_val = self.pre_processor.gibberish_word_generator(str_val, all_existing_chars, german=german)
                    input_vals.append(input_val[0])
                    target_vals.append(target_val)
        print("Training-sample Length ", len(input_vals))
        print(input_vals[:100])
        print(target_vals[:100])
        encode_max_length = max([len(i) for i in input_vals])
        decode_max_length = max([len(i) for i in target_vals])
        print("Max word length Encoded set: ", encode_max_length)
        print("Max word lenght Decoded set: ", decode_max_length)
        return input_vals, target_vals, encode_max_length, decode_max_length

    @staticmethod
    def create_zero_vectors(input_vals, encode_max_length, decoded_max_length, all_existing_chars):

       #all_existing_chars = list(" abcdefghijklmnopqrstuvwxyz0123456789")

        # define the length of the sample to train the model
        training_sample_length = len(input_vals)

        print("length of all existing chars: ", len(all_existing_chars))
        print(all_existing_chars)

        # create 3d-arrays
        encoder_input_data = np.zeros((training_sample_length, encode_max_length, len(all_existing_chars)), dtype='float32')

        # add 2 for the \t and \n Star/Stop tokens
        decoder_input_data = np.zeros((training_sample_length, decoded_max_length, len(all_existing_chars) + 2), dtype='float32')
        decoder_target_data = np.zeros((training_sample_length, decoded_max_length, len(all_existing_chars) + 2), dtype='float32')

        print("Sucessfully created zero vectors for encoder and decoder.")
        return encoder_input_data, decoder_input_data, decoder_target_data

    # filling in the "real" encoded and decoded data in the vector structure
    @staticmethod
    def fill_data_arrays(input_vals, target_vals, encoder_input_data, decoder_input_data, decoder_target_data, char_int_dict):

        for i, (input_val, target_val) in enumerate(zip(input_vals, target_vals)):
            for t, char in enumerate(input_val):
                encoder_input_data[i, t, char_int_dict[char]] = 1.0
            for t, char in enumerate(target_val):
                decoder_input_data[i, t, char_int_dict[char]] = 1.0
                if t > 0:
                    decoder_target_data[i, t - 1, char_int_dict[char]] = 1.0

            decoder_input_data[i, t + 1:, char_int_dict[' ']] = 1.0
            decoder_target_data[i, t:, char_int_dict[' ']] = 1.0

        print("Data Array filling complete")
        return encoder_input_data, decoder_input_data, decoder_target_data

    @staticmethod
    def fill_data_arrays_2(input_vals, target_vals, encoder_input_data, decoder_input_data, decoder_target_data,char_int_dict):

        input_token_index = dict([(char, i) for i, char in enumerate(char_int_dict)])
        target_token_index = dict([(char, i) for i, char in enumerate(char_int_dict)])

        print("input_token_index :", input_token_index)

        for i, (input_val, target_val) in enumerate(zip(input_vals, target_vals)):
            for t, char in enumerate(input_val):
                encoder_input_data[i, t, input_token_index[char]] = 1.0
            encoder_input_data[i, t + 1:, input_token_index[" "]] = 1.0
            for t, char in enumerate(target_val):
                # decoder_target_data is ahead of decoder_input_data by one timestep
                decoder_input_data[i, t, target_token_index[char]] = 1.0
                if t > 0:
                    # decoder_target_data will be ahead by one timestep
                    # and will not include the start character.
                    decoder_target_data[i, t - 1, target_token_index[char]] = 1.0
            decoder_input_data[i, t + 1:, target_token_index[" "]] = 1.0
            decoder_target_data[i, t:, target_token_index[" "]] = 1.0

        return encoder_input_data, decoder_input_data, decoder_target_data

    @staticmethod
    def create_ml_model_with_tuning(batch_size, epochs, all_existing_chars, encoder_input_data, decoder_input_data,
                                    decoder_target_data):
        def build_model(hp):
            dropout_rate = hp.Float('dropout_rate', min_value=0.2, max_value=0.5, step=0.1)
            latent_dim = hp.Int('latent_dim', min_value=32, max_value=256, step=32)

            num_enc_tokens = len(all_existing_chars)
            num_dec_tokens = len(all_existing_chars) + 2  # includes \n \t

            encoder_inputs = Input(shape=(None, num_enc_tokens))
            encoder = LSTM(latent_dim, return_state=True, recurrent_dropout=dropout_rate)
            encoder_outputs, state_h, state_c = encoder(encoder_inputs)
            encoder_states = [state_h, state_c]

            decoder_inputs = Input(shape=(None, num_dec_tokens))
            decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True, recurrent_dropout=dropout_rate)
            decoder_outputs, _, _ = decoder_lstm(decoder_inputs, initial_state=encoder_states)
            decoder_dense = Dense(num_dec_tokens, activation='softmax')
            decoder_outputs = decoder_dense(decoder_outputs)

            model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
            model.compile(optimizer="rmsprop", loss='categorical_crossentropy', metrics=['accuracy'])
            return model

        tuner = RandomSearch(
            build_model,
            objective='val_loss',
            max_trials=10,
            executions_per_trial=1,
            directory='tuning_directory',
            project_name='seq2seq_tuning'
        )

        tuner.search([encoder_input_data, decoder_input_data], decoder_target_data,
                     epochs=epochs,
                     batch_size=batch_size,
                     validation_split=0.3)

        best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]
        model = tuner.hypermodel.build(best_hps)

        model.fit([encoder_input_data, decoder_input_data], decoder_target_data,
                  epochs=epochs,
                  batch_size=batch_size,
                  validation_split=0.3)

        model.save('savedModels/tuned_model_128batch.h5')

        return model


    @staticmethod
    def create_ml_model(batch_size,epochs,latent_dim, all_existing_chars, encoder_input_data, decoder_input_data, decoder_target_data):

        dropout_rate = 0.4

        num_enc_tokens = len(all_existing_chars)
        num_dec_tokens = len(all_existing_chars) + 2  # includes \n \t

        encoder_inputs = Input(shape=(None, num_enc_tokens))
        encoder = LSTM(latent_dim, return_state=True, recurrent_dropout=dropout_rate)
        encoder_outputs, state_h, state_c = encoder(encoder_inputs)

        encoder_states = [state_h, state_c]

        decoder_inputs = Input(shape=(None, num_dec_tokens))
        decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True, recurrent_dropout=dropout_rate)
        decoder_outputs, _, _ = decoder_lstm(decoder_inputs, initial_state=encoder_states)

        decoder_dense = Dense(num_dec_tokens, activation='softmax')
        decoder_outputs = decoder_dense(decoder_outputs)

        # define callback function for EarlyStopping
        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

        # define the ReduceLROnPlateau-Callback
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=3, min_lr=0.00001)

        model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
        #optimizer = RMSprop(learning_rate=0.001)
        model.compile(optimizer="adam", loss='categorical_crossentropy', metrics=['accuracy'])
        model.summary()

        model.fit([encoder_input_data, decoder_input_data], decoder_target_data,
                  epochs=epochs,
                  batch_size=batch_size,
                  validation_split=0.25,
                  callbacks=[early_stopping, reduce_lr]
                  )

        model.save('savedModels/312Dim_96Batch_adam_german_uml_15epochs_moreData.h5')
        model.save('savedModels/312Dim_96Batch_adam_german_uml_15epochs_moreData.keras')

        encoder_model = Model(encoder_inputs, encoder_states)

        decoder_state_input_h = Input(shape=(latent_dim,))
        decoder_state_input_c = Input(shape=(latent_dim,))
        decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
        decoder_outputs, state_h, state_c = decoder_lstm(
            decoder_inputs, initial_state=decoder_states_inputs
        )
        decoder_states = [state_h, state_c]
        decoder_outputs = decoder_dense(decoder_outputs)
        decoder_model = Model(
            [decoder_inputs] + decoder_states_inputs,
            [decoder_outputs] + decoder_states
        )
        encoder_model.save('savedModels/encoder_312Dim_96Batch_adam_german_uml_15epochs_moreData.h5')
        decoder_model.save('savedModels/decoder_312Dim_96Batch_adam_german_uml_15epochs_moreData.h5')

    @staticmethod
    def create_ml_model_2(batch_size, epochs, latent_dim, all_existing_chars, encoder_input_data, decoder_input_data,decoder_target_data):

        num_enc_tokens = len(all_existing_chars)
        num_dec_tokens = len(all_existing_chars) + 2  # includes \n \t

        # Define an input sequence and process it.
        encoder_inputs = tf.keras.Input(shape=(None, num_enc_tokens))
        encoder = tf.keras.layers.LSTM(latent_dim, return_state=True, dropout=0.3)
        encoder_outputs, state_h, state_c = encoder(encoder_inputs)

        # We discard `encoder_outputs` and only keep the states.
        encoder_states = [state_h, state_c]

        # Set up the decoder, using `encoder_states` as initial state.
        decoder_inputs = tf.keras.Input(shape=(None, num_dec_tokens))

        # We set up our decoder to return full output sequences,
        # and to return internal states as well. We don't use the
        # return states in the training model, but we will use them in inference.
        decoder_lstm = tf.keras.layers.LSTM(latent_dim, return_sequences=True, return_state=True, dropout=0.3)
        decoder_outputs, _, _ = decoder_lstm(decoder_inputs, initial_state=encoder_states)
        decoder_dense = tf.keras.layers.Dense(num_dec_tokens, activation="softmax")
        decoder_outputs = decoder_dense(decoder_outputs)

        # Define the model
        # `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
        model = tf.keras.Model([encoder_inputs, decoder_inputs], decoder_outputs)

        model.compile(
            optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

        # define callback function for EarlyStopping
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

        model.fit(
            [encoder_input_data, decoder_input_data],
            decoder_target_data,
            batch_size=batch_size,
            epochs=epochs,
            validation_split=0.2,
            callbacks=[early_stopping]
        )

        model.save("savedModels/new_test_model_4.h5")
        model.save("savedModels/new_test_model_4_keras.keras")


    @staticmethod
    def doPredict(input_seq, model_to_load, latent_dim, char_int_dict, all_existing_chars, decode_max_length):
        model = tf.keras.models.load_model(model_to_load)

        input_token_index = dict([(char, i) for i, char in enumerate(char_int_dict)])
        target_token_index = dict([(char, i) for i, char in enumerate(char_int_dict)])

        num_dec_tokens = len(all_existing_chars) + 2  # adding  \n \t

        encoder_inputs = model.input[0]
        encoder_outputs, state_h_enc, state_c_enc = model.layers[2].output
        encoder_states = [state_h_enc, state_c_enc]
        encoder_model = tf.keras.Model(encoder_inputs, encoder_states)

        decoder_inputs = model.input[1]
        decoder_state_input_h = tf.keras.Input(shape=(latent_dim,), name="input_3")
        decoder_state_input_c = tf.keras.Input(shape=(latent_dim,), name="input_4")
        decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
        decoder_lstm = model.layers[3]
        decoder_outputs, state_h_dec, state_c_dec = decoder_lstm(
            decoder_inputs, initial_state=decoder_states_inputs
        )
        decoder_states = [state_h_dec, state_c_dec]
        decoder_dense = model.layers[4]
        decoder_outputs = decoder_dense(decoder_outputs)
        decoder_model = tf.keras.Model(
            [decoder_inputs] + decoder_states_inputs, [decoder_outputs] + decoder_states
        )

        reverse_input_char_index = dict((i, char) for char, i in input_token_index.items())
        reverse_target_char_index = dict((i, char) for char, i in target_token_index.items())

        def predict_with_temperature(temperature):
            # Encode the input as state vectors.
            states_value = encoder_model.predict(input_seq)

            # Generate empty target sequence of length 1.
            target_seq = np.zeros((1, 1, num_dec_tokens))
            # Populate the first character of target sequence with the start character.
            target_seq[0, 0, target_token_index["\t"]] = 1.0

            stop_condition = False
            decoded_sentence = ""
            confidence_score = 0.0

            while not stop_condition:
                output_tokens, h, c = decoder_model.predict([target_seq] + states_value)

                output_tokens = output_tokens[0, -1, :]
                output_tokens = np.log(output_tokens + 1e-8) / temperature
                exp_preds = np.exp(output_tokens)
                output_tokens = exp_preds / np.sum(exp_preds)

                sampled_token_index = np.random.choice(range(len(output_tokens)), p=output_tokens)
                sampled_char = reverse_target_char_index[sampled_token_index]
                decoded_sentence += sampled_char

                # Update the confidence score by adding the log probability of the sampled token
                confidence_score += np.log(output_tokens[sampled_token_index])

                if sampled_char == "\n" or len(decoded_sentence) > decode_max_length:
                    stop_condition = True

                # Update the target sequence (of length 1).
                target_seq = np.zeros((1, 1, num_dec_tokens))
                target_seq[0, 0, sampled_token_index] = 1.0

                # Update states
                states_value = [h, c]

            confidence_score = np.exp(confidence_score)
            return decoded_sentence, confidence_score

        # Initial parameters
        temperature = 0.7
        confidence_threshold = 0.8
        max_attempts = 4
        attempts = 0

        # First prediction attempt
        decoded_sentence, confidence_score = predict_with_temperature(temperature)

        # Adjust temperature and retry if necessary
        while confidence_score < confidence_threshold and attempts < max_attempts:
            print(f"Low confidence score: {confidence_score:.2f}. for word: {decoded_sentence} Retrying with adjusted temperature.")
            temperature *= 0.5  # Reduce the temperature to make predictions more deterministic
            decoded_sentence, confidence_score = predict_with_temperature(temperature)
            attempts += 1

        return decoded_sentence, confidence_score
