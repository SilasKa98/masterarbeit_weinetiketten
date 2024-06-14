import cv2
import numpy as np


class ImageModificationService:

    def __init__(self, image_path):
        self.image_path = image_path
        self.image_src = cv2.imread(self.image_path)
        if self.image_src is None:
            raise ValueError(f"Couldn't load image! {image_path}")

    def image_rescaler(self):
        self.image_src = cv2.resize(self.image_src, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
        return self

    def image_grayscaler(self):
        self.image_src = cv2.cvtColor(self.image_src, cv2.COLOR_BGR2GRAY)
        return self

    def noise_remover(self):
        kernel = np.ones((1, 1), np.uint8)
        self.image_src = cv2.dilate(self.image_src, kernel, iterations=1)
        self.image_src = cv2.erode(self.image_src, kernel, iterations=1)
        return self

    def blur_apply(self, filter_type):

        if 'gaussian' in filter_type:
            cv2.threshold(cv2.GaussianBlur(self.image_src, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            cv2.adaptiveThreshold(cv2.GaussianBlur(self.image_src, (5, 5), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                              31, 2)

        if 'bilateral' in filter_type:
            cv2.threshold(cv2.bilateralFilter(self.image_src, 5, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            cv2.adaptiveThreshold(cv2.bilateralFilter(self.image_src, 9, 75, 75), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, 31, 2)

        if 'median' in filter_type:
            cv2.threshold(cv2.medianBlur(self.image_src, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            cv2.adaptiveThreshold(cv2.medianBlur(self.image_src, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

        return self

    def save_modified_image(self, save_path):

        cv2.imwrite(save_path, self.image_src)
        print('Successfully saved Image ' + save_path)




