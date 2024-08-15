import json
import os
import threading
import uuid
from collections import OrderedDict

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename


class InterfaceService:

    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.tasks = {}  # Dictionary to track all running tasks

    def run(self):
        self.handlers()
        self.app.run(debug=True)

    def handlers(self):

        @self.app.route('/status', methods=['GET'])
        def get_all_task_status():
            return jsonify(self.tasks)

        @self.app.route('/status/<task_name>', methods=['GET'])
        def get_task_status(task_name):
            if task_name in self.tasks:
                return jsonify(self.tasks[task_name])
            else:
                return jsonify({"status": "unknown", "name": "unknown"})

        @self.app.route('/test', methods=['POST'])
        def read_ocr():
            data = request.json
            param = data.get('param', None)
            response = {
                "status": "success",
                "parameter_received": param,
                "data_received": data
            }
            return jsonify(response)

        @self.app.route('/spelling_correction', methods=['POST'])
        def spelling_correction():
            data = request.json
            table = data["table"]
            sel_columns = data["sel_columns"]
            insert_column = data["insert_column"]
            use_ml = data["use_ml"]
            lang_filter = data["lang_filter"]
            only_new = data["only_new"]
            if lang_filter == "None":
                lang_filter = None
            task_id = str(uuid.uuid4())
            task_name = "spelling_correction"

            sel_columns = sel_columns + ", " + table + ".path"


            # use threads so the task is getting done async and the rest of the system stays responsive
            threading.Thread(target=self.process_spelling_correction,
                             args=(task_id, task_name, table, sel_columns, insert_column, use_ml, lang_filter, only_new)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)

        @self.app.route('/update_label_detail_infos', methods=['POST'])
        def update_label_detail_infos():

            task_id = str(uuid.uuid4())
            task_name = "update_label_detail_infos"

            threading.Thread(target=self.process_update_label_detail_infos, args=(task_id, task_name)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)

        @self.app.route('/search_for_duplicate_entrys', methods=['POST'])
        def search_for_duplicate_entrys():
            data = request.json
            table = data["table"]
            column = data["column"]
            save = data["save"]
            save_table = "duplicates"
            task_id = str(uuid.uuid4())
            task_name = "search_for_duplicate_entrys"

            threading.Thread(target=self.process_search_for_duplicate_entrys,
                             args=(task_id, task_name, table, column, save, save_table)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)

        @self.app.route('/read_and_save_ocr', methods=['POST'])
        def read_and_save_ocr():
            data = request.json
            table = data["table"]
            ocr_model = data["table"]
            column = data["column"]
            path = data["path"]
            use_translation = data["use_translation"]
            only_new_entries = data["only_new_entries"]
            task_id = str(uuid.uuid4())
            task_name = "read_and_save_ocr"

            threading.Thread(target=self.process_read_and_save_ocr,
                             args=(task_id, task_name, table, ocr_model, column, path, use_translation, only_new_entries)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)

        @self.app.route('/read_db_and_detect_lang', methods=['POST'])
        def read_db_and_detect_lang():
            data = request.json
            force_update = data["force_update"]
            task_id = str(uuid.uuid4())
            task_name = "read_db_and_detect_lang"

            threading.Thread(target=self.process_read_db_and_detect_lang,
                             args=(task_id, task_name, force_update)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)

        @self.app.route('/search_algorithm', methods=['POST'])
        def search_algorithm():
            data = request.json
            search_text = data["search_text"]
            search_logic_combined = data["search_logic_combined"]
            task_id = str(uuid.uuid4())
            task_name = "search_algorithm"

            threading.Thread(target=self.process_search_algorithm, args=(task_id, task_name, search_text, search_logic_combined)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)


        @self.app.route('/get_image_informations', methods=['POST'])
        def get_image_informations():
            data = request.json
            path = data["path"]
            task_id = str(uuid.uuid4())
            task_name = "get_image_informations"
            threading.Thread(target=self.process_get_image_informations, args=(task_id, task_name, path)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)


        @self.app.route('/modify_images', methods=["POST"])
        def modify_images():
            data = request.json
            directory = data["directory"]
            task_id = str(uuid.uuid4())
            task_name = "modify_images"
            threading.Thread(target=self.process_modify_images, args=(task_id, task_name, directory)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)

        @self.app.route('/check_directory_for_duplicates', methods=["POST"])
        def check_directory_for_duplicates():
            if 'images' not in request.files:
                return "no files have been uploaded!", 400

            images = request.files.getlist('images')

            # save files which need to be checked for dups to upload folder
            # TODO put in .env
            UPLOAD_FOLDER = 'C:\Masterarbeit_ocr_env\duplicate_check_upload'
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            for file in images:
                # check if filename exists and is secure
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    try:
                        file.save(file_path)
                        print(f"file saved: {file_path}")
                    except Exception as e:
                        print(f"error while saving {filename}: {e}")

            task_id = str(uuid.uuid4())
            task_name = "check_directory_for_duplicates"
            threading.Thread(target=self.process_check_directory_for_duplicates, args=(task_id, task_name, UPLOAD_FOLDER)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)

        @self.app.route('/update_entities_for_labels', methods=["POST"])
        def update_entities_for_labels():
            task_id = str(uuid.uuid4())
            task_name = "update_entities_for_labels"
            threading.Thread(target=self.process_update_entities_for_labels, args=(task_id, task_name)).start()

            self.tasks[task_name] = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "name": task_name
            }
            return jsonify(response)


    # ------------------------------------------------Processing--------------------------------------------------------
    # functions to async handle the processing
    def process_spelling_correction(self, task_id, task_name, table, sel_columns, insert_column, use_ml, lang_filter, only_new):

        from ActionProcessor import ActionProcessor
        action_processor = ActionProcessor()
        action_processor.correct_sentence_spelling(table, sel_columns, insert_column, use_ml=use_ml, lang_filter=lang_filter, only_new=only_new)

        self.tasks[task_name] = {"status": "success",
                                 "name": task_name,
                                 "task_id": task_id
                                 }

    def process_update_label_detail_infos(self, task_id, task_name):
        from ActionProcessor import ActionProcessor
        action_processor = ActionProcessor()
        action_processor.update_label_detail_infos()

        self.tasks[task_name] = {"status": "success",
                                 "name": task_name,
                                 "task_id": task_id
                                 }

    def process_search_for_duplicate_entrys(self, task_id, task_name, table, column, save, save_table):

        from ActionProcessor import ActionProcessor
        action_processor = ActionProcessor()
        similarity_result = action_processor.search_for_duplicate_entrys(table, column, save=save, save_table=save_table)

        return_strings = []
        for item in similarity_result:
            # extract paths out of the tupels
            path1 = item[3][0] if isinstance(item[3], tuple) else item[3]
            path2 = item[4][0] if isinstance(item[4], tuple) else item[4]

            append_string = f"<p>Ratio: {item[2]} | Paths: <a href=/{path1} target='_blank'>{path1}</a> & <a href=/{path2} target='_blank'>{path2}</a></p>"
            return_strings.append(append_string)

        self.tasks[task_name] = {"status": "success",
                                 "name": task_name,
                                 "task_id": task_id,
                                 "result": return_strings
                                 }

    def process_read_and_save_ocr(self, task_id, task_name, table, ocr_model, column, path, use_translation, only_new_entries):

        from ActionProcessor import ActionProcessor
        action_processor = ActionProcessor()

        # edit path to suit the desired format
        path_parts = os.path.normpath(path).split(os.sep)
        start_index = path_parts.index('wine_images')
        trimmed_path = os.path.join(*path_parts[start_index:])
        path = trimmed_path.replace(os.sep, '/')
        if not path.endswith('/'):
            path += '/'

        action_processor.read_and_save_ocr(ocr_model, path, table, column,
                                           use_translation=use_translation, only_new_entrys=only_new_entries)

        self.tasks[task_name] = {"status": "success",
                                 "name": task_name,
                                 "task_id": task_id
                                 }

    def process_read_db_and_detect_lang(self, task_id, task_name, force_update):

        from ActionProcessor import ActionProcessor
        action_processor = ActionProcessor()
        action_processor.read_db_and_detect_lang(force_update=force_update)

        self.tasks[task_name] = {"status": "success",
                                 "name": task_name,
                                 "task_id": task_id
                                 }

    def process_search_algorithm(self, task_id, task_name, search_text, search_logic_combined):
        from Services.SearchImagesService import SearchImagesService
        from Services.DataProcessService import DataProcessService
        search = SearchImagesService()
        search_results = search.search_algorithm(search_text, search_logic_combined)
        top_hits = search_results[0]
        second_choice_hits = search_results[1]
        text_based_hits = search_results[2]

        for key in top_hits:
            top_hits[key] = list(top_hits[key])

        hits = {"top_hits": top_hits,  "text_based_hits": text_based_hits, "second_choice_hits": second_choice_hits}

        data_processing = DataProcessService()
        hits = data_processing.convert_set_to_list(hits)

        self.tasks[task_name] = {
            "status": "success",
            "name": task_name,
            "task_id": task_id,
            "result": hits
        }

    def process_get_image_informations(self, task_id, task_name, path):
        from Services.DatabaseService import DatabaseService
        database = DatabaseService()
        db_results = database.select_from_table("etiketten_infos", "*", condition="path = %s", params=[path])
        print("frontend_db_results")
        print(db_results)
        image_name = db_results[0][2]
        image_lang = db_results[0][4]
        image_directory = db_results[0][5]
        image_country = db_results[0][6]
        image_provinces = db_results[0][7]
        image_anno = db_results[0][8]
        image_vol = db_results[0][9]
        image_wine_type = db_results[0][10]

        result = {"image_name": image_name,
                  "image_lang": image_lang,
                  "image_directory": image_directory,
                  "image_country": image_country,
                  "image_provinces": image_provinces,
                  "image_anno": image_anno,
                  "image_vol": image_vol,
                  "image_wine_type": image_wine_type
                  }

        self.tasks[task_name] = {
            "status": "success",
            "name": task_name,
            "task_id": task_id,
            "result": result
        }

    def process_modify_images(self, task_id, task_name, directory):
        from ActionProcessor import ActionProcessor
        action = ActionProcessor()
        action.modify_images(directory)

        self.tasks[task_name] = {
            "status": "success",
            "name": task_name,
            "task_id": task_id
        }

    def process_check_directory_for_duplicates(self, task_id, task_name, upload_folder):

        from ActionProcessor import ActionProcessor
        action = ActionProcessor()
        found_duplicates = action.check_directory_for_duplicates(upload_folder=upload_folder)
        print(found_duplicates)

        return_strings = []
        for item in found_duplicates:
            # extract paths out of the tupels
            path1 = item[3][0] if isinstance(item[3], tuple) else item[3]
            path2 = item[4][0] if isinstance(item[4], tuple) else item[4]

            append_string = f"<p>Ratio: {item[2]} | Paths: <a href=/{path1} target='_blank'>{path1}</a> & <a href=/{path2} target='_blank'>{path2}</a></p>"
            return_strings.append(append_string)

        # after everything is done, clear the upload folder
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
        else:
            print(f"Upload folder {upload_folder} does not exist.")

        self.tasks[task_name] = {
            "status": "success",
            "name": task_name,
            "task_id": task_id,
            "result": return_strings
        }

    def process_update_entities_for_labels(self, task_id, task_name):
        from ActionProcessor import ActionProcessor
        action = ActionProcessor()
        action.update_entities_for_labels()

        self.tasks[task_name] = {
            "status": "success",
            "name": task_name,
            "task_id": task_id
        }




