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
           # all_directorys_db = self.database_service.select_from_table("etiketten_infos", "image_directory")
           # all_directorys_db = {dire[0] for dire in all_directorys_db}

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

            # some path modifications to match each other
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
            elif "doctr" in ocr_model:
                image_string = self.doctr_service.read_in_files(image_path)

            # WIP needs to be adressed. What happens if ocr recognizes nothing?
            if image_string == "":
                image_string = "empty"

            # printing current path for better overview
            print(image_path)

            directory_results.append([image_string,image_path,image_name, detected_lang, image_directory_name])
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
                self.database_service.update_table(
                    "etiketten_infos",
                    ["detected_language", "image_directory", "read_in_date"],
                    [image_info[3], image_info[4], current_time_formatted],
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

    def search_for_duplicate_entrys(self, search_table, search_column, save=False, save_table=''):
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

    def correct_sentence_spelling(self, table, column_text, insert_column, use_ml=False, lang_filter=None):
        if lang_filter is None:
            condition = None
            spellchecker_lang = "en"
        else:
            condition = f"etiketten_infos.detected_language = '{lang_filter}'"
            spellchecker_lang = lang_filter
        select_result_text = self.database_service.select_from_table(table,
                                                                     column_text,
                                                                     join=f"left join etiketten_infos ON {table}.path = etiketten_infos.path",
                                                                     condition=condition
                                                                     )
        print(select_result_text[:3])
        cleaned_string_list = [result[0] for result in select_result_text]

        if lang_filter == "de":
            additional_dict = "dictionary_files/german_extracted_words_20mio_uml.txt"
        else:
            additional_dict = "dictionary_files/empty_dict.txt"

        spell = SpellcheckerService(additional_dict, spellchecker_lang)
        spell.add_words_to_spellchecker_dict()

        pre_processor = PreProcessor()
        if use_ml:
            machine_learning = MachineLearningService('german_extracted_words_750k_uml.txt', '256Dim_96Batch_adam_german_newTrainingData_uml2.h5')
            ml_correction_init = machine_learning.ml_word_correction_init(pre_processor.form_dataframe_german_txt)

        for idx, item in enumerate(cleaned_string_list):
            modified_sentence = []

            item_words = item.split()
            for word in item_words:
                cleaned_word = pre_processor.word_cleaning(word)
                cleaned_word = pre_processor.remove_numerics(cleaned_word)
                special_characters = "!@#$%^&*()+?_=,<>/"
                if len(cleaned_word) > 1:
                    if use_ml:
                        if len(cleaned_word) > 5 and not any(char in special_characters for char in cleaned_word) and not cleaned_word.isdigit():
                            is_word_correct = spell.is_word_correct_check(cleaned_word)

                            if not is_word_correct[0]:
                                modified_word = machine_learning.ml_word_correction_exec(cleaned_word, 256, ml_correction_init[0], ml_correction_init[1], ml_correction_init[2], ml_correction_init[3])
                                modified_sentence.append(modified_word)
                            else:
                                modified_sentence.append(word)
                        else:
                            modified_sentence.append(word)
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





