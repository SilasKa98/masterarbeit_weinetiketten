import re

from Services.DataProcessService import DataProcessService
from Services.DeepLService import DeepLService
from Services.TesseractService import TesseractService
from Services.DatabaseService import DatabaseService
from Services.EasyOCRService import EasyOCRService
from Models.word_spelling_correction.PreProcessor import PreProcessor
from Services.MachineLearningService import MachineLearningService
from Services.ImageModificationService import ImageModificationService
from Services.DoctrService import DoctrService
from Services.SpellcheckerService import SpellcheckerService
from Services.DetailFinderService import DetailFinderService
import os
from collections import defaultdict
from datetime import datetime
import easyocr


class ActionProcessor:

    def __init__(self):
        self.data_process_service = DataProcessService()
        self.deepl_service = DeepLService()
        self.tesseract_service = TesseractService()
        self.database_service = DatabaseService()
        self.easy_ocr_service = EasyOCRService()
        self.doctr_service = DoctrService()

    def process_directory(self, directory_input, use_translation, ocr_model, only_new_entrys=False):

        # directory_input = directory path
        images = self.data_process_service.iterate_directory(directory_input)
        # iterate images in paths
        directory_results = []

        # removing the edited_wine_images paths if only the normal directory is given, otherwise it would scan the
        # images double. Once normal and once edited, even if they are treated as one in the db (no extra path entrys
        # for edited images)
        if "edited_wine_images" not in directory_input:
            images = (image_path for image_path in images if 'edited_wine_images' not in image_path)

        if only_new_entrys:
            all_sub_directorys = self.data_process_service.get_subdirectories("wine_images/")
            all_sub_directorys.remove("edited_wine_images")
            print(all_sub_directorys)
            # check if a subfolder/specific-directory is given in the path e.g. wineimages/archiv19/
            # sql calls get handle different if specific subfolder is given
            is_specific_directory = False
            for directory in all_sub_directorys:
                if directory in directory_input:
                    db_filter_directory = directory
                    is_specific_directory = True

            if is_specific_directory:
                all_paths_in_db_tupels = self.database_service.select_from_table("etiketten_infos", "path",
                                                                                 "image_directory=%s",
                                                                                 [db_filter_directory])
            else:
                all_paths_in_db_tupels = self.database_service.select_from_table("etiketten_infos", "path")

            # some path modifications to get them in the correct format
            all_paths_in_db = {path[0] for path in all_paths_in_db_tupels}
            all_paths_in_db_normalized = [path.replace('\\', '/') for path in all_paths_in_db]
            images_normalized = [path.replace('\\', '/') for path in images]

            # if edited_wine_images in given path input, add substring to db paths so the check for only_new_entrys
            # is still working as expected
            if "edited_wine_images" in directory_input:
                all_paths_in_db_normalized = [path.split('/', 1)[0] + '/edited_wine_images/' + path.split('/', 1)[1] if '/' in path else path for path in all_paths_in_db_normalized]

            images = (image_path for image_path in images_normalized if image_path not in all_paths_in_db_normalized)

        for index, image_path in enumerate(images):

            image_directory = os.path.dirname(os.path.abspath(image_path))
            image_directory_name = os.path.basename(image_directory)
            image_name = os.path.basename(image_path)

            if use_translation is True:
                # atm. tesseract is used always to generate a first string for a possible language detection.
                # However most languages are already in the db and so it doesn't really matter because its ignored then.
                string_for_detection = self.tesseract_service.read_in_files(image_path, "unknown")
                detected_lang = self.deepl_service.detect_language(string_for_detection, image_name, image_directory_name)
                detected_lang_iso639_1 = self.deepl_service.deepl_to_iso639_1(detected_lang)
                detected_lang_iso639_2 = self.deepl_service.deepl_to_iso639_2(detected_lang)
            else:
                detected_lang_iso639_1 = "unknown"
                detected_lang_iso639_2 = "unknown"

            if "tesseract" in ocr_model:
                image_string = self.tesseract_service.read_in_files(image_path, detected_lang_iso639_2)
            elif "easyocr" in ocr_model:
                image_string = self.easy_ocr_service.read_in_files(image_path, detected_lang_iso639_1)
            elif "doctr" in ocr_model:
                image_string = self.doctr_service.read_in_files(image_path)

            # WIP needs to be adressed. What happens if ocr recognizes nothing?
            if image_string == "":
                image_string = "empty"

            # printing current path for better overview
            print(image_path)

            directory_results.append([image_string,image_path,image_name, detected_lang_iso639_1, image_directory_name])
        return directory_results

    def read_and_save_ocr(self, ocr_model, path_to_read, table, column_addition, use_translation=False, only_new_entrys=False):
        action_processor = ActionProcessor()
        # use_translation True / False determines  wether language knowledge is used for ocr or not
        image_reads = action_processor.process_directory(path_to_read, use_translation, ocr_model, only_new_entrys)
        self.database_service = DatabaseService()

        for image_info in image_reads:
            if 'edited_wine_images' in image_info[1]:
                image_info[1] = image_info[1].replace('/edited_wine_images/', '\\')
            # replace all / for \ so its correct for checking in the db
            image_info[1] = image_info[1].replace('/', '\\')

            # first check the etiketten_infos table if the image is already existing there.
            # If not insert, otherwise update the corresponding informations
            select_result = self.database_service.select_from_table("etiketten_infos", "id", "path=%s", [image_info[1]])
            current_time = datetime.now()
            current_time_formatted = current_time.strftime('%Y-%m-%d %H:%M:%S')
            if not select_result:
                print (image_info[1], "is not in etiketteninfos! tying to insert...")
                self.database_service.insert_into_table(
                    "etiketten_infos",
                    ["path", "name", "detected_language", "image_directory", "read_in_date"],
                    [image_info[1], image_info[2], image_info[3], image_info[4], current_time_formatted]
                )
            else:
                # when language got detected update it, if its unknown rather keep the current value in the database
                if image_info[3] != "unknown":
                    update_cols = ["detected_language", "image_directory", "read_in_date"]
                    update_params = [image_info[3], image_info[4], current_time_formatted]
                else:
                    update_cols = ["image_directory", "read_in_date"]
                    update_params = [image_info[4], current_time_formatted]

                self.database_service.update_table(
                    "etiketten_infos",
                    update_cols,
                    update_params,
                    "path",
                    image_info[1]
                )

            # now check for the actual used ocr table if there is already a entry for the processed image
            # if so update, otherwise insert
            select_result = self.database_service.select_from_table(table, "*", "path=%s", [image_info[1]])
            if len(select_result) == 0:
                self.database_service.insert_into_table(
                    table,
                    [f"text_{column_addition}", "path"],
                    [image_info[0], image_info[1]]
                )

            else:
                self.database_service.update_table(
                    table,
                    [f"text_{column_addition}"],
                    [image_info[0]],
                    "path",
                    image_info[1]
                )

    def read_db_and_detect_lang(self, force_update=False):
        select_result = self.database_service.select_from_table("etiketten_infos as et",
                                                                "et.name, et.image_directory, et.path, dr.text_pure",
                                                                join="left join doctr as dr on et.path = dr.path"
                                                                )
        for entry in select_result:
            name = entry[0]
            image_directory = entry[1]
            image_path = entry[2]
            text = entry[3]
            detected_lang = self.deepl_service.detect_language(text, name, image_directory, force_update=force_update)
            detected_lang = self.deepl_service.deepl_to_iso639_1(detected_lang)
            print('updating language (',detected_lang,') for image: ', image_path, '\n')
            self.database_service.update_table(
                "etiketten_infos",
                ["detected_language"],
                [detected_lang],
                "path",
                image_path
            )

    def search_for_duplicate_entrys(self, search_table, search_column, save=False, save_table='duplicates'):
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

    def correct_sentence_spelling(self, table, column_text, insert_column, use_ml=False, lang_filter=None, only_new=False):

        # check if the selected language is in supported langs (langs where a model is available)
        # if not present, set ml to false, because it would make results worse
        #lang_support_ml = ["de", "fr", "it", "en"]
        #if lang_filter not in lang_support_ml:
          #  use_ml = False

        if lang_filter is None:
            if only_new:
                condition = f'{table}.{insert_column} = ""'
            else:
                condition = None
        else:
            if only_new:
                condition = f'etiketten_infos.detected_language = "{lang_filter}"'
            else:
                condition = f'etiketten_infos.detected_language = "{lang_filter}" and {table}.{insert_column} = ""'

        select_result_text = self.database_service.select_from_table(table,
                                                                     f'{column_text}, detected_language',
                                                                     join=f"left join etiketten_infos ON {table}.path = etiketten_infos.path",
                                                                     condition=condition
                                                                     )
        print(select_result_text[:3])
        cleaned_string_list = [result[0] for result in select_result_text]
        fetched_langs = [result[2] for result in select_result_text]

        spell_de = SpellcheckerService('dictionary_files\\german_extracted_words_20mio_uml.txt', language="de")
        spell_de.add_words_to_spellchecker_dict()

        spell_en = SpellcheckerService('dictionary_files\\english_extracted_words_20mio_uml_en.txt', language="en")
        spell_en.add_words_to_spellchecker_dict()

        spell_fr = SpellcheckerService('dictionary_files\\french_extracted_words_20mio_uml_fr.txt', language="fr")
        spell_fr.add_words_to_spellchecker_dict()

        spell_it = SpellcheckerService('dictionary_files\\italy_extracted_words_20mio_uml_it.txt', language="it")
        spell_it.add_words_to_spellchecker_dict()

        pre_processor = PreProcessor()
        if use_ml:
            machine_learning_de = MachineLearningService('german_extracted_words_750k_uml.txt', '256Dim_96Batch_adam_german_newTrainingData_uml2.h5')
            ml_correction_init_de = machine_learning_de.ml_word_correction_init(pre_processor.form_dataframe_german_txt, language="de")

            machine_learning_en = MachineLearningService('english_extracted_words_750k_uml_en.txt', '312Dim_96Batch_adam_english_uml.h5')
            ml_correction_init_en = machine_learning_en.ml_word_correction_init(pre_processor.form_dataframe_german_txt, language="en")

            machine_learning_it = MachineLearningService('italy_extracted_words_750k_uml_it.txt', '312Dim_96Batch_adam_italian_uml_2.h5')
            ml_correction_init_it = machine_learning_it.ml_word_correction_init(pre_processor.form_dataframe_german_txt, language="it")

            machine_learning_fr = MachineLearningService('french_extracted_words_750k_uml_fr.txt', '312Dim_96Batch_adam_french_uml_2.h5')
            ml_correction_init_fr = machine_learning_fr.ml_word_correction_init(pre_processor.form_dataframe_german_txt, language="fr")

        for idx, item in enumerate(cleaned_string_list):
            modified_sentence = []

            item_words = item.split()
            for word in item_words:
                deepl = DeepLService()
                word_lang = deepl.detect_language_on_the_fly(word)
                if word_lang[1] >= 0.9:
                    word_lang = word_lang[0]
                else:
                    word_lang = fetched_langs[idx]

                if word_lang == "de":
                    spell = spell_de
                elif word_lang == "en":
                    spell = spell_en
                elif word_lang == "fr":
                    spell = spell_fr
                elif word_lang == "it":
                    spell = spell_it
                else:
                    spell = SpellcheckerService(added_dict_file="", language="")

                cleaned_word = pre_processor.word_cleaning(word, lang=word_lang)
                cleaned_word = pre_processor.remove_numerics(cleaned_word)
                special_characters = "!@#$%^&*()+?_=,<>/"
                if len(cleaned_word) > 1:
                    if use_ml:
                        if len(cleaned_word) > 5 and not any(char in special_characters for char in cleaned_word) and not cleaned_word.isdigit():
                            is_word_correct = spell.is_word_correct_check(cleaned_word)
                            if not is_word_correct[0]:
                                modified_word = cleaned_word
                                iteration_count = 0
                                max_iterations = 5
                                while not spell.is_word_correct_check(modified_word)[0]:
                                    if word_lang == "de":
                                        modified_word = machine_learning_de.ml_word_correction_exec(cleaned_word, 256 ,ml_correction_init_de[0],ml_correction_init_de[1],ml_correction_init_de[2],ml_correction_init_de[3])
                                    elif word_lang == "fr":
                                        modified_word = machine_learning_fr.ml_word_correction_exec(cleaned_word, 312,ml_correction_init_fr[0],ml_correction_init_fr[1],ml_correction_init_fr[2],ml_correction_init_fr[3])
                                    elif word_lang == "it":
                                        modified_word = machine_learning_it.ml_word_correction_exec(cleaned_word, 312, ml_correction_init_it[0],ml_correction_init_it[1],ml_correction_init_it[2],ml_correction_init_it[3])
                                    else:
                                        modified_word = machine_learning_en.ml_word_correction_exec(cleaned_word, 312,ml_correction_init_en[0],ml_correction_init_en[1],ml_correction_init_en[2],ml_correction_init_en[3])
                                    modified_word = re.sub(r'\s+', '', modified_word)
                                    iteration_count += 1
                                    if iteration_count >= max_iterations:
                                        break
                                # if new correct word seems to be found in the 5 iterations append it, else try to
                                # correct with spellcorrection
                                if iteration_count < 5:
                                    modified_sentence.append(modified_word)
                                else:
                                    modified_word = spell.correct_word(cleaned_word)
                                    modified_sentence.append(modified_word)
                            else:
                                modified_sentence.append(word)
                        else:
                            modified_word = spell.correct_word(cleaned_word)
                            modified_sentence.append(modified_word)
                    else:
                        modified_word = spell.correct_word(cleaned_word)
                        modified_sentence.append(modified_word)

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

    def update_label_detail_infos(self):
        all_paths_in_db_tupels = self.database_service.select_from_table("etiketten_infos", "path")
        all_paths_in_db = {path[0] for path in all_paths_in_db_tupels}
        all_paths_in_db_normalized = [path.replace('/', '\\') for path in all_paths_in_db]
        details = DetailFinderService()
        for item in all_paths_in_db_normalized:
            print(item)
            vol = details.find_vol(item)
            anno = details.find_anno(item)
            countries = ', '.join(list(set(details.find_country(item))))
            provinces = ', '.join(list(set(details.find_provinces(item))))
            self.database_service.update_table("etiketten_infos",
                                               ["country", "provinces", "anno", "vol"],
                                               [countries, provinces, anno, vol],
                                               "path",
                                               item
                                               )





