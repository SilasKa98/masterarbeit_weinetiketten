import random

import matplotlib.pyplot as plt
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os
import re
from gibberish import Gibberish


class PreProcessor:

    @staticmethod
    def form_dataframe(input_file):
        # Load file with correct words
        df = pd.read_csv(input_file,)
        print(df.shape)

        df = df.drop(df.columns[0], axis=1)
        df = df.drop('description', axis=1)
        df = df.drop('points', axis=1)
        df = df.drop('price', axis=1)
        print(df)
        # drop all rows with missing values
        df.dropna(axis=0, how='any')
        print(df.shape)
        combined_data = []
        for value in df.itertuples():
            combined_data.append(value[0])
            combined_data.append(value[1])
            combined_data.append(value[2])
            combined_data.append(value[3])
            combined_data.append(value[4])
            combined_data.append(value[5])
            combined_data.append(value[6])

        # filter nan and digits
        combined_data = [x for x in combined_data if str(x) != 'nan']
        combined_data = [x for x in combined_data if not isinstance(x, int)]
        combined_data = [element for element in combined_data if not element.isdigit()]

        regex_numbers = re.compile(r'\d+')
        combined_data = [element for element in combined_data if not regex_numbers.search(element)]


        combined_single_words_data = []
        for item in combined_data:
            if " " in item:
                combined_single_words_data.extend(item.split())
            else:
                combined_single_words_data.append(item)

        combined_df_data = {'word': combined_single_words_data}
        combined_df = pd.DataFrame(combined_df_data)

        print(combined_df.shape)
        print(combined_df.head())
        return combined_df

    def form_dataframe_german(self, input_file):
        df = pd.read_csv(input_file, low_memory=False)

        df = df.filter(['!'])
        df = df.rename(columns={"!": "word"})
        df = df.map(self.remove_numerics)
        df['word'] = df['word'].str.replace('\d+', '', regex=True)
        # df['word'] = df['word'].str.replace('\W', '', regex=True)
        df = df.dropna()
        empty_filter = df["word"] != ""
        df = df[empty_filter]
        zero_filter = df["word"] != "0"
        df = df[zero_filter]
        #df = df.map(self.word_cleaning(german=True))
        df = df.map(lambda x: self.word_cleaning(x, german=True))
        print(df.head())
        return df

    def form_dataframe_english(self, input_file):

        df = pd.read_csv(input_file, low_memory=False)
        df = df.filter(['word'])
        df = df.map(self.remove_numerics)
        df['word'] = df['word'].str.replace('\d+', '', regex=True)
        df['word'] = df['word'].str.replace('\W', '', regex=True)
        df = df.dropna()
        empty_filter = df["word"] != ""
        df = df[empty_filter]
        zero_filter = df["word"] != "0"
        df = df[zero_filter]
        df = df.map(self.word_cleaning)
        print(df.head())
        return df

    def form_dataframe_vivno(self, input_file):
        df = pd.read_csv(input_file, encoding="utf-16")
        df = df.filter(['Names'])
        df = df.rename(columns={"Names": "word"})
        df = df.map(self.remove_numerics)
        df['word'] = df['word'].str.replace('\d+', '', regex=True)
        df = df.dropna()
        print(df.head())

        '''
        df = pd.read_csv(input_file, sep=',', quotechar='"', encoding='utf-8')
        print(df)
        print(df.head())
        
        df = df.filter(['Names'])
        
        df = df.rename(columns={"Names": "word"})
        df = df.map(self.remove_numerics)
        df = df.dropna()
        empty_filter = df["word"] != ""
        df = df[empty_filter]
        df = df.map(self.word_cleaning)
        print(df.head())
        '''

        return df

    @staticmethod
    def remove_numerics(x):
        if isinstance(x, (int, float)):
            return np.nan
        else:
            return x

    # load a csv file and transform it to a pandas dataframe
    @staticmethod
    def load_data(input_file):
        # Load file with correct words
        df  = pd.read_csv(input_file)
        print(df.shape)

        # drop all rows with missing values
        df.dropna(axis=0,how='any')
        print(df.shape)
        return df

    # count all lines of the dataframe but also check if the value of the line is a string
    @staticmethod
    def count_lines(dataframe):
        string_lines = []
        for string in dataframe['word']:
            if isinstance(string, str):
                string_lines.append(string)

        print("Number of Lines: ", len(string_lines))
        return string_lines

    # function to clean a input string -> lower all chars + remove all numbers and upper case chars + replace \n with ''
    @staticmethod
    def word_cleaning(input_val, german=False):
        input_val = input_val.lower()
        if not german:
            input_val = re.sub(r'[^0-9a-zA-Z ]','',input_val)
        else:
            input_val = re.sub(r'[^0-9a-zA-ZäöüÄÖÜ ]', '', input_val)
        input_val = input_val.replace('\n','')
        return input_val

    def word_splitting(self, input_list):
        string_lines = [self.word_cleaning(val) for val in input_list]
        splitted_words = []
        for str_line in string_lines:
            splitted_words += [val_split for val_split in str_line.split()]
        string_lines = list(set(splitted_words))
        print("\n".join(string_lines[:4]))
        print("Number of words:", len(string_lines))
        return string_lines

    @staticmethod
    def char_indexing(all_existing_chars):
        # all_existing_chars = list(" abcdefghijklmnopqrstuvwxyz0123456789")
        all_existing_specials = ['\n', '\t', '#']
        char_int_dict = {}
        int_char_dict = {}
        for index, char in enumerate(all_existing_chars):
            int_char_dict[index] = char
            char_int_dict[char] = index

        dict_length = len(int_char_dict)
        for i in range(len(all_existing_specials)):
            int_char_dict[dict_length] = all_existing_specials[i]
            char_int_dict[all_existing_specials[i]] = dict_length
            dict_length = dict_length+1

        print(int_char_dict)
        print(char_int_dict)
        return int_char_dict, char_int_dict

    @staticmethod
    def gibberish_word_generator(input_word, german=False):

        num_cases = random.randint(1,5)
        input_fanned = list(input_word)

        all_existing_chars = list(" abcdefghijklmnopqrstuvwxyzüöä0123456789")
        for _ in range(num_cases):
            cases = random.randint(1, 6)
            # case to add a random char to the original string
            if cases == 1:
                random_char_index = random.randint(0, len(input_word) - 1)

                input_fanned.insert(random_char_index,random.choice(all_existing_chars))
                gib_word = ''.join(input_fanned)
                return gib_word, input_word

            # case to delete a random char of the original string
            elif cases == 2:
                random_char_index = random.randint(0, len(input_word) - 1)
                del input_fanned[random_char_index]
                gib_word = ''.join(input_fanned)
                return gib_word, input_word

            # case to replace a char
            elif cases == 3:
                random_char_index = random.randint(0, len(input_word) - 1)
                input_fanned[random_char_index] = random.choice(all_existing_chars)
                gib_word = ''.join(input_fanned)
                return gib_word, input_word

            # special case for german to replace ü with u , ä with a and ö with o else--> random replace like in case3
            elif cases == 4:
                if german:
                    gib_word = ''
                    special_characters = ['ü', 'ö', 'ä']
                    replace_characters = ['u', 'o', 'a']
                    for index, char in enumerate(input_fanned):
                        if char in special_characters:
                            special_char_index = special_characters.index(char)
                            input_fanned[index] = replace_characters[special_char_index]
                            gib_word = ''.join(input_fanned)
                    if gib_word == '':
                        random_char_index = random.randint(0, len(input_word) - 1)
                        input_fanned[random_char_index] = random.choice(all_existing_chars)
                        gib_word = ''.join(input_fanned)
                else:
                    random_char_index = random.randint(0, len(input_word) - 1)
                    input_fanned[random_char_index] = random.choice(all_existing_chars)
                    gib_word = ''.join(input_fanned)

                return gib_word, input_word

            # another special case for german to delete ü ö and ä from words, bcs of their week detection rate in ocr
            elif cases == 5:
                if german:
                    special_characters = ['ü', 'ö', 'ä']
                    for index, char in enumerate(input_fanned):
                        if char in special_characters:
                            special_char_index = special_characters.index(char)
                            del input_fanned[special_char_index]
                else:
                    random_char_index = random.randint(0, len(input_word) - 1)
                    del input_fanned[random_char_index]

                gib_word = ''.join(input_fanned)
                return gib_word, input_word

            # case to scramble 2 chars
            else:
                random_char_index1 = random.randint(0, len(input_word) - 1)
                random_char_index2 = random.randint(0, len(input_word) - 1)
                while random_char_index1 == random_char_index2:
                    random_char_index2 = random.randint(0, len(input_word) - 1)

                random_char1 = input_fanned[random_char_index1]
                random_char2 = input_fanned[random_char_index2]

                input_fanned[random_char_index1] = random_char2
                input_fanned[random_char_index2] = random_char1

                gib_word = ''.join(input_fanned)
                return gib_word, input_word




