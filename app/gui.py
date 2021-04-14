
from autoaim import helpers, Camera, Config, Predictor
from toolz import pipe, curry
import cv2
import time
import numpy as np
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QSlider, QLabel, QHBoxLayout, QLineEdit


class CameraThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, source, method, resolution):
        super().__init__()
        self.camera = Camera(source, method).init(resolution)
        self.delay = 200

    def run(self):
        while True:
            success, image = self.camera.get_image()
            if success:
                # image = cv2.resize(image, (0, 0), fx=1.5, fy=1.5)
                self.signal.emit(image)
                time.sleep(self.delay/1000)


class QSetting(QWidget):
    def __init__(self, name, scope, default, callback):
        super(QSetting, self).__init__()

        self.callback = callback

        self.layout = QHBoxLayout()
        # self.layout.addStretch(1)

        self.label = QLabel(name)
        self.layout.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setTickPosition(QSlider.TicksLeft)
        self.slider.setRange(*scope)
        self.slider.setValue(default)
        self.slider.valueChanged.connect(self.slider_value_changed)
        self.layout.addWidget(self.slider)

        self.textbox = QLineEdit(self)
        self.layout.addWidget(self.textbox)
        self.textbox.setFixedWidth(50)
        self.textbox.setText(str(default))
        self.textbox.textChanged.connect(self.textbox_value_changed)

        self.setLayout(self.layout)

        self.lock = False

    def slider_value_changed(self, value):
        self.textbox.setText(str(value))
        self.callback(value)

    def textbox_value_changed(self, value):
        self.slider.setValue(int(value))


class DisplayImageWidget(QWidget):
    def __init__(self, callback=None):
        super(DisplayImageWidget, self).__init__()

        self.layout = QVBoxLayout()

        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_capture)
        self.layout.addWidget(self.start_button)

        self.image_frame = QLabel()
        self.layout.addWidget(self.image_frame)

        self.setLayout(self.layout)

        self.config = Config().data
        self.predictor = Predictor(self.config)
        self.camera_thread = CameraThread(0, 'daheng', (1280, 1024))
        self.toolbox = self.predictor.toolbox
        self.callback = callback
        self.image = None

    def start_capture(self):
        if self.callback is not None:
            self.callback()
        self.start_button.setParent(None)
        self.camera_thread.signal.connect(self.show_image)
        self.camera_thread.start()

    def set_delay(self, value):
        self.camera_thread.delay = 1000/value
        self.update()

    def set_hsv(self, value):
        self.config['hsv_lower_value'] = value
        self.update()

    def show_image(self, image):
        self.image = image
        if image.shape[0]:
            # image = self.process(image)
            image = cv2.resize(image, (0, 0), fx=0.1, fy=0.1)
            image = QImage(
                image.tobytes(), image.shape[1], image.shape[0], QImage.Format_RGB888).rgbSwapped()
            self.image_frame.setPixmap(QPixmap.fromImage(image))

    def update(self):
        if self.image is not None:
            self.show_image(self.image)

    def process(self, img):
        self.predictor.predict(img)
        return img
        # return pipe(cv2.resize(img, (0, 0), fx=0.5, fy=0.5),
        # self.toolbox.draw_contours,
        # self.toolbox.draw_bounding_rects,
        # self.toolbox.draw_pair_bounding_rects,
        # self.toolbox.draw_pair_index,
        # self.toolbox.draw_pair_bounding_text()(
        #     lambda p: '{0}:{1:.1f}'.format(
        #         p['y_label'], p['y_max']),
        #     text_position='bottom'
        # ),
        # )


class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoAim Console")

        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.widget_image = DisplayImageWidget()
        self.layout.addWidget(self.widget_image)

        self.delay_setting = QSetting(
            'fps', (1, 100), 10, self.widget_image.set_delay)
        self.layout.addWidget(self.delay_setting)

        self.hsv_setting = QSetting(
            'hsv', (46, 255), 100, self.widget_image.set_hsv)
        self.layout.addWidget(self.hsv_setting)


if __name__ == '__main__':
    app = QApplication([])
    window = StartWindow()
    window.show()
    app.exit(app.exec_())
