import math
import pprint

import cv2
import numpy as np
import mmcv
from mmocr.apis import MMOCRInferencer
import matplotlib
matplotlib.use('TkAgg')


class MMOCRService:

    @staticmethod
    def calculate_orientation(polygon):
        points = [(polygon[i], polygon[i + 1]) for i in range(0, len(polygon), 2)]

        def length(p1, p2):
            return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

        max_length = 0
        longest_side = None
        for i in range(len(points)):
            p1, p2 = points[i], points[(i + 1) % len(points)]
            l = length(p1, p2)
            if l > max_length:
                max_length = l
                longest_side = (p1, p2)

        if longest_side is None:
            return None

        dx = longest_side[1][0] - longest_side[0][0]
        dy = longest_side[1][1] - longest_side[0][1]
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        angle_deg = abs(angle_deg)
        if angle_deg > 90:
            angle_deg = 180 - angle_deg

        return angle_deg

    def choose_detection_model(self, image_path, confidence_filter):
        ocr = MMOCRInferencer(det='DBNet', rec="SAR")  # Oder ein anderes Modell wie DBNet
        results = ocr(image_path)

        all_orientations = []
        for prediction in results['predictions']:
            for i, text in enumerate(prediction['rec_texts']):
                if prediction['rec_scores'][i] > confidence_filter:
                    polygon = prediction['det_polygons'][i]
                    orientation = self.calculate_orientation(polygon)
                    all_orientations.append(orientation)

        all_words_count = len(prediction['rec_texts'])
        if all_words_count > 0:
            avg_angle = sum(all_orientations) / all_words_count
        else:
            avg_angle = 0
        print("avg_angle: ", avg_angle)
        if avg_angle > 20:
            return "TextSnake"
        else:
            return "DBNet"

    def read_in_files(self, read_in_image, variable_detection=True):
        confidence_filter = 0.8
        if variable_detection:
            chosen_det_model = self.choose_detection_model(read_in_image, confidence_filter)
        else:
            chosen_det_model = "DBNet"
        print("chosen_model: ", chosen_det_model)
        ocr = MMOCRInferencer(det=chosen_det_model, rec='SAR')
        results = ocr(read_in_image)
        if chosen_det_model == "TextSnake":
            ocr_check = MMOCRInferencer(det="DBNet", rec='SAR')
            results_check = ocr_check(read_in_image)

            filtered_results = [x for x in results['predictions'][0]['det_scores'] if x > 0.8]
            filtered_results_check = [x for x in results_check['predictions'][0]['det_scores'] if x > 0.8]
            if len(filtered_results) > 0 and len(filtered_results_check) > 0:
                results_avg_score = sum(filtered_results) / len(filtered_results)
                results_check_avg_score = sum(filtered_results_check) / len(filtered_results_check)

                print("results_check_avg_score: ", results_check_avg_score)
                print("results_avg_score: ", results_avg_score)
                if results_check_avg_score > results_avg_score:
                    results = results_check
                    print("switch from TextSnake to DBNet")

        texts = []
        for prediction in results['predictions']:
            for i, text in enumerate(prediction['rec_texts']):
                if prediction['det_scores'][i] > confidence_filter:
                    texts.append((text, prediction['det_polygons'][i]))

        def get_min_x(polygon):
            return min(polygon[::2])

        def get_min_y(polygon):
            return min(polygon[1::2])

        def get_avg_x(polygon):
            return sum(polygon[::2]) / (len(polygon) // 2)

        def get_avg_y(polygon):
            return sum(polygon[1::2]) / (len(polygon) // 2)

        #sorted_texts = sorted(texts, key=lambda x: (get_min_y(x[1]), get_min_x(x[1])))
        sorted_texts = sorted(texts, key=lambda x: (get_avg_y(x[1]), get_avg_x(x[1])))

        if sorted_texts:
            y_tolerance = 40
            final_sorted_texts = []
            current_line = []
            current_y = get_min_y(sorted_texts[0][1])

            # sort text
            for text, polygon in sorted_texts:
                min_y = get_min_y(polygon)

                if abs(min_y - current_y) <= y_tolerance:
                    current_line.append((text, polygon))
                else:
                    current_line_sorted = sorted(current_line, key=lambda x: get_min_x(x[1]))
                    final_sorted_texts.extend([text for text, _ in current_line_sorted])

                    current_line = [(text, polygon)]
                    current_y = min_y

            current_line_sorted = sorted(current_line, key=lambda x: get_min_x(x[1]))
            final_sorted_texts.extend([text for text, _ in current_line_sorted])
        else:
            final_sorted_texts = texts

        return ' '.join(final_sorted_texts)

