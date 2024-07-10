import threading
import uuid
from flask import Flask, request, jsonify


class InterfaceService:

    def __init__(self):
        self.app = Flask(__name__)
        self.tasks = {}  # Dictionary to track all running tasks

    def run(self):
        self.handlers()
        self.app.run(debug=True)

    def handlers(self):
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
            task_id = str(uuid.uuid4())

            # use threads so the task is getting done async and the rest of the system stays responsive
            threading.Thread(target=self.process_spelling_correction,
                             args=(task_id, table, sel_columns, insert_column, use_ml, lang_filter)).start()

            self.tasks[task_id] = {
                "status": "processing",
                "message": "process running..."
            }

            response = {
                "task_id": task_id,
                "status": "processing",
                "message": "process running..."
            }
            return jsonify(response)

        @self.app.route('/status', methods=['GET'])
        def get_all_task_status():
            return jsonify(self.tasks)

        @self.app.route('/status/<task_id>', methods=['GET'])
        def get_task_status(task_id):
            if task_id in self.tasks:
                return jsonify(self.tasks[task_id])
            else:
                return jsonify({"status": "error", "message": "Task ID not found"}), 404

    # function to async handle the processing
    def process_spelling_correction(self, task_id, table, sel_columns, insert_column, use_ml, lang_filter):

        from ActionProcessor import ActionProcessor
        action_processor = ActionProcessor()
        action_processor.correct_sentence_spelling(table, sel_columns, insert_column, use_ml=use_ml, lang_filter=lang_filter)

        self.responses[task_id] = {"status": "success",
                                   "message": "Process finished."}
