# main.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox,
    QToolBar
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Slot
import pyvista as pv
from pyvistaqt import QtInteractor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FEA Uygulaması MVP")
        self.setGeometry(100, 100, 900, 700)

        # Menü Çubuğu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Dosya")
        view_menu = menubar.addMenu("&Görünüm")

        # "Aç..." eylemi
        open_action = QAction("&Aç...", self)
        open_action.setStatusTip("Bir mesh dosyası aç (.STL, .VTK vb.)")
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)

        # "Çıkış" eylemi
        exit_action = QAction("&Çıkış", self)
        exit_action.setStatusTip("Uygulamadan çık")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Araç Çubuğu
        toolbar = QToolBar("Kamera Kontrolleri")
        self.addToolBar(toolbar)

        # Kamera kontrol eylemleri
        front_action = QAction("Ön", self)
        front_action.setStatusTip("Ön görünüm")
        front_action.triggered.connect(self.view_front)
        toolbar.addAction(front_action)

        top_action = QAction("Üst", self)
        top_action.setStatusTip("Üst görünüm")
        top_action.triggered.connect(self.view_top)
        toolbar.addAction(top_action)

        right_action = QAction("Sağ", self)
        right_action.setStatusTip("Sağ görünüm")
        right_action.triggered.connect(self.view_right)
        toolbar.addAction(right_action)

        isometric_action = QAction("İzometrik", self)
        isometric_action.setStatusTip("İzometrik görünüm")
        isometric_action.triggered.connect(self.view_isometric)
        toolbar.addAction(isometric_action)

        # "Reset" eylemi
        reset_action = QAction("Reset", self)
        reset_action.setStatusTip("Kamerayı sıfırla")
        reset_action.triggered.connect(self.reset_camera)
        toolbar.addAction(reset_action)

        # Merkezi bir widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Ana düzen
        main_layout = QVBoxLayout(central_widget)

        # PyVista Plotter
        self.plotter = QtInteractor(central_widget)
        main_layout.addWidget(self.plotter.interactor)

        # Başlangıçta sahne
        self.plotter.add_axes()
        self.plotter.camera_position = 'iso'
        self.plotter.reset_camera()

    @Slot()
    def open_file_dialog(self):
        file_filter = "Mesh Dosyaları (*.stl *.vtk *.vtu *.ply *.obj);;Tüm Dosyalar (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Mesh Dosyası Aç", "", file_filter)

        if file_path:
            self.load_mesh(file_path)

    def load_mesh(self, file_path):
        try:
            mesh = pv.read(file_path)
            self.plotter.clear()
            self.plotter.add_mesh(mesh, show_edges=True, color="lightblue")
            self.plotter.reset_camera()
            QMessageBox.information(self, "Başarılı", f"{file_path} başarıyla yüklendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Mesh dosyası yüklenirken bir hata oluştu:\n{e}")

    def view_front(self):
        self.plotter.view_vector((0, -1, 0))

    def view_top(self):
        self.plotter.view_vector((0, 0, 1))

    def view_right(self):  # Sağ görünüm
        self.plotter.view_vector((1, 0, 0))

    def view_isometric(self):
        self.plotter.view_isometric()

    # Reset metodu
    def reset_camera(self):
        # Kamerayı izometrik görünüme ayarla
        self.plotter.view_isometric()
        # Kamerayı sıfırla
        self.plotter.reset_camera()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())