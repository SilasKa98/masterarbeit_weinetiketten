from Services.DataProcessService import DataProcessService
from Services.DeepLService import DeepLService
from Services.TesseractService import TesseractService
from Services.DatabaseService import DatabaseService
from Services.EasyOCRService import EasyOCRService
from Models.word_spelling_correction.PreProcessor import PreProcessor
from Services.MachineLearningService import MachineLearningService
from Services.ImageModificationService import ImageModificationService
import os
from collections import defaultdict
import easyocr


class ActionProcessor:

    def __init__(self):
        self.data_process_service = DataProcessService()
        self.deepl_service = DeepLService()
        self.tesseract_service = TesseractService()
        self.database_service = DatabaseService()
        self.easy_ocr_service = EasyOCRService()

    def process_directory(self, directory_input, use_translation, ocr_model):

        # directory_input = directory path
        images = self.data_process_service.iterate_directory(directory_input)
        # iterate images in paths
        directory_results = []

        for index, image_path in enumerate(images):
            #if index == 100:
                #break
            image_directory = os.path.dirname(os.path.abspath(image_path))
            image_directory_name = os.path.basename(image_directory)
            image_name = os.path.basename(image_path)

            if use_translation is True:
                # atm. tesseract is used always to generate a first string for a possible language detection.
                # However most languages are already in the db and so it doesn't really matter because its ignored then.
                string_for_detection = self.tesseract_service.read_in_files(image_path, "unknown")
                detected_lang = self.deepl_service.detect_language(string_for_detection, image_name, image_directory_name)
            else:
                detected_lang = "unknown"

            if "tesseract" in ocr_model:
                if use_translation is True:
                    detected_lang = self.deepl_service.deepl_to_iso639_2(detected_lang)
                image_string = self.tesseract_service.read_in_files(image_path, detected_lang)
            elif "easyocr" in ocr_model:
                if use_translation is True:
                    detected_lang = self.deepl_service.deepl_to_iso639_1(detected_lang)
                image_string = self.easy_ocr_service.read_in_files(image_path, detected_lang)

            # WIP needs to be adressed. What happens if ocr recognizes nothing?
            if image_string == "":
                image_string = "empty"

            # printing current path for better overview
            print(image_path)

            directory_results.append([image_string,image_path,image_name, detected_lang, image_directory_name])
        return directory_results

    def read_and_save_ocr(self, ocr_model, path_to_read, table, column_addition):
        action_processor = ActionProcessor()
        # True / False determines  wether translation is used for ocr or not
        image_reads = action_processor.process_directory(path_to_read, False, ocr_model)
        self.database_service = DatabaseService()

        for image_info in image_reads:
            if 'edited_wine_images' in image_info[1]:
                image_info[1] = image_info[1].replace('/edited_wine_images/', '\\')
            if table == "etiketten_infos":
                select_result = self.database_service.select_from_table(table, "*", "name=%s", [image_info[2]])
                if not select_result:
                    self.database_service.insert_into_table(
                        table,
                        [f"text_{column_addition}", "path", "name", "detected_language", "image_directory"],
                        [image_info[0], image_info[1], image_info[2], image_info[3], image_info[4]]
                    )
                else:
                    self.database_service.update_table(
                        table,
                        [f"text_{column_addition}", "path", "detected_language", "image_directory"],
                        [image_info[0], image_info[1], image_info[3], image_info[4]],
                        "name",
                        image_info[2]
                    )
            else:
                select_result = self.database_service.select_from_table(table, "*", "path=%s", [image_info[1]])
                print(select_result)
                if len(select_result) == 0:
                    '''
                    self.database_service.insert_into_table(
                        table,
                        [f"text_{column_addition}", "path"],
                        [image_info[0], image_info[1]]
                    )
                    '''
                    continue
                else:
                    self.database_service.update_table(
                        table,
                        [f"text_{column_addition}"],
                        [image_info[0]],
                        "path",
                        image_info[1]
                    )

    def read_db_and_detect_lang(self):
        self.database_service = DatabaseService()
        select_result = self.database_service.select_from_table("etiketten_infos", "name, image_directory, path, text_tesseract, text_easyocr")
        #print(select_result)
        for entry in select_result:
            name = entry[0]
            image_directory = entry[1]
            image_path = entry[2]
            text_tesseract = entry[3]
            text_easyocr = entry[4]
            joined_texts = text_tesseract + text_easyocr
            detected_lang = self.deepl_service.detect_language(joined_texts, name, image_directory)
            print('updating language for image: ',image_path, '\n')
            self.database_service.update_table(
                "etiketten_infos",
                ["detected_language"],
                [detected_lang],
                "path",
                image_path
            )

    def search_for_duplicate_entrys(self, search_table, search_column, save=False, save_table=''):
        self.database_service = DatabaseService()
        select_result_text = self.database_service.select_from_table(search_table, search_column)
        select_result_path = self.database_service.select_from_table(search_table, 'path')

        similarity_result = self.data_process_service.find_similar_sentences(select_result_text, select_result_path, 80)
        path_dup_dict = defaultdict(list)
        ratio_dup_dict = defaultdict(list)
        for item in similarity_result:
            print("ratio: ", item[2], "Paths: ", item[3], "&", item[4])
            path_dup_dict[item[3][0]].append(item[4][0])
            ratio_dup_dict[item[3][0]].append(item[2])

        for k, v in path_dup_dict.items():
            if save:
                select_result_insert = self.database_service.select_from_table(save_table, 'og_path, found_in_table', 'og_path=%s', [k])
                if select_result_insert:
                    found_in_table_current = select_result_insert[0][1]
                    if search_table not in found_in_table_current:
                        found_in_table_new = found_in_table_current +' , ' + search_table
                    else:
                        found_in_table_new = found_in_table_current
                    self.database_service.update_table(
                        save_table,
                        ['dup_paths', 'confidence_ratios', 'found_in_table'],
                        [' , '.join(path_dup_dict[k]), ' , '.join(map(str, ratio_dup_dict[k])), found_in_table_new],
                        "og_path",
                        k
                    )
                else:
                    print([k, path_dup_dict[k], ratio_dup_dict[k]])
                    self.database_service.insert_into_table(
                        save_table,
                        ['og_path', 'dup_paths', 'confidence_ratios', 'found_in_table'],
                        [k, ' , '.join(path_dup_dict[k]), ' , '.join(map(str, ratio_dup_dict[k])), search_table]
                    )

        return similarity_result

    def correct_sentence_with_ml(self, table, column_text, insert_column):
        self.database_service = DatabaseService()
        language_filter = "de"
        select_result_text = self.database_service.select_from_table(table,
                                                                     column_text,
                                                                     join=f"left join etiketten_infos ON {table}.path = etiketten_infos.path",
                                                                     condition=f"etiketten_infos.detected_language = '{language_filter}'"
                                                                     )
        print(select_result_text[:3])
        cleaned_string_list = [result[0] for result in select_result_text]

        pre_processor = PreProcessor()
        machine_learning = MachineLearningService('german_words', '256Dim_512Batch_adam_german_specialChars_newGib_v2')
        ml_correction_init = machine_learning.ml_word_correction_init(pre_processor.form_dataframe_german)

        for idx, item in enumerate(cleaned_string_list):
            modified_sentence = []

            item_words = item.split()
            for word in item_words:
                cleaned_word = pre_processor.word_cleaning(word)
                cleaned_word = pre_processor.remove_numerics(cleaned_word)
                special_characters = "!@#$%^&*()-+?_=,<>/"
                if len(cleaned_word) > 6 and not any(char in special_characters for char in cleaned_word):
                    modified_word = machine_learning.ml_word_correction_exec(cleaned_word, 256, ml_correction_init[0], ml_correction_init[1], ml_correction_init[2], ml_correction_init[3])
                    modified_sentence.append(modified_word)
                else:
                    modified_sentence.append(word)
            print(modified_sentence)
            joined_string = ' '.join(modified_sentence)
            print(joined_string)
            current_path = select_result_text[idx][1]
            self.database_service.update_table(
                table,
                [insert_column],
                [joined_string],
                "path",
                current_path
            )

    def modify_images(self, directory_path):

        images = self.data_process_service.iterate_directory(directory_path)
        print(images)
        for index, img_path in enumerate(images):
            image_directory = os.path.dirname(os.path.abspath(img_path))
            image_directory_name = os.path.basename(image_directory)
            image_name = os.path.basename(img_path)

            image_mod = ImageModificationService(image_directory+"/"+image_name)
            processed_path = f"C:/Masterarbeit_ocr_env/wine_images/edited_wine_images/{image_directory_name}"
            if not os.path.exists(processed_path):
                os.makedirs(processed_path)

            save_path = processed_path + f"/{image_name}"
            print(image_mod.get_image_dpi())
            if image_mod.get_image_dpi()[0] >= 300 and image_mod.get_image_dpi()[1] >= 300:
                print("dpi > 300")
                image_mod.image_grayscaler().noise_remover().blur_apply("median").save_modified_image2(save_path)
            else:
                print("dpi < 300")
                image_mod.image_grayscaler().image_rescaler().noise_remover().blur_apply("median")\
                    .save_modified_image2(save_path)

    def process_single_picuture(self, image_path):

        print("ImagePath: ")
        print(image_path)
        print("\n")
        print("---------processing 1-----------")
        print("\n")
        image_string = self.tesseract_service.read_in_files(image_path, "unknown")
        print(image_string)
        detected_lang = self.deepl_service.detect_language(image_string)
        print("detected language:" + detected_lang)
        print("\n")
        print("---------processing 2-----------")
        print("\n")
        image_string = self.tesseract_service.read_in_files(image_path, detected_lang)
        print(image_string)
        print("\n")
        return image_string, image_path
