import cv2
import numpy as np
from PIL import Image

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

    def bump_contrast(self):
        mean, std_dev = cv2.meanStdDev(self.image_src)
        mean = mean[0][0]
        std_dev = std_dev[0][0]

        # Dynamische Berechnung von alpha und beta
        alpha = 1.0 + (0.05 * (127 - std_dev) / 127)   # Wert anpassen, um den Kontrast dynamisch zu erhöhen
        beta = 5 * (127 - mean) / 127   # Wert anpassen, um die Helligkeit dynamisch zu korrigieren

        # Anwendung der Kontrast- und Helligkeitsanpassung
        self.image_src = cv2.convertScaleAbs(self.image_src, alpha=alpha, beta=beta)

        # Histogrammausgleich, um den Kontrast zu verbessern
        #self.image_src = cv2.equalizeHist(self.image_src)
        return self

    def sharpen_img(self):
        # Unsharp Masking
        gaussian_blur = cv2.GaussianBlur(self.image_src, (5, 5), 5.0)
        self.image_src = cv2.addWeighted(self.image_src, 2.0, gaussian_blur, -1.0, 0)

        # Normalisierung, um die Helligkeit zu kontrollieren
        self.image_src = cv2.normalize(self.image_src, None, 0, 255, cv2.NORM_MINMAX)
        return self

    def adaptive_threshold(self):
        self.image_src= cv2.adaptiveThreshold(self.image_src, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, 73, 2)
        return self

    def noise_remover(self):
        kernel = np.ones((1, 1), np.uint8)
        self.image_src = cv2.dilate(self.image_src, kernel, iterations=1)
        self.image_src = cv2.erode(self.image_src, kernel, iterations=1)

        return self

    def blur_apply(self, filter_type="median"):

        if 'gaussian' in filter_type:
            self.image_src = cv2.GaussianBlur(self.image_src, (5, 5), 0)
        elif 'bilateral' in filter_type:
            self.image_src = cv2.bilateralFilter(self.image_src, 9, 75, 75)
        elif 'median' in filter_type:
            self.image_src = cv2.medianBlur(self.image_src, 3)
        else:
            raise ValueError("Unsupported filter type: Choose from 'gaussian', 'bilateral', or 'median'")
        return self

    def save_modified_image(self, save_path):

        cv2.imwrite(save_path, self.image_src)
        print('Successfully saved Image ' + save_path)

    def save_modified_image2(self, save_path):

        original_image_pil = Image.open(self.image_path)
        dpi = original_image_pil.info.get('dpi', (300, 300))  # set dpi to 300x300 if info not available

        # Konvertiere das OpenCV-Bild zu einem Pillow-Image
        image_pil = Image.fromarray(cv2.cvtColor(self.image_src, cv2.COLOR_BGR2RGB))
        image_pil.save(save_path, dpi=dpi)
        print('Successfully saved Image ' + save_path)

    def get_image_dpi(self):
        with Image.open(self.image_path) as img:
            dpi = img.info.get('dpi')
            if dpi:
                return dpi
            else:
                return (0, 0)








