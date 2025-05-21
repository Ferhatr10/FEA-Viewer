# main.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox,
    QHBoxLayout, QPushButton, QLabel, QLineEdit, QFormLayout, QDialog, QDialogButtonBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Slot, Qt # Qt.WindowModal için
import pyvista as pv
from pyvistaqt import QtInteractor

# -----------------------------------------------------------------------------
# Kamera Ayarları Diyalog Penceresi
# -----------------------------------------------------------------------------
class CameraSettingsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Kamera Ayarları")
        # self.setWindowModality(Qt.WindowModal) # Ana pencereyi blokla

        self.current_settings = current_settings if current_settings else {}

        layout = QFormLayout(self)

        self.front_input = QLineEdit(self.current_settings.get("front", "0,0,-1"))
        self.back_input = QLineEdit(self.current_settings.get("back", "0,0,1"))
        self.top_input = QLineEdit(self.current_settings.get("top", "0,1,0"))
        self.isometric_input = QLineEdit(self.current_settings.get("iso", "iso"))

        layout.addRow(QLabel("Ön Görünüm Vektörü:"), self.front_input)
        layout.addRow(QLabel("Arka Görünüm Vektörü:"), self.back_input)
        layout.addRow(QLabel("Üst Görünüm Vektörü:"), self.top_input)
        layout.addRow(QLabel("İzometrik Kamera Pozisyonu:"), self.isometric_input)

        # Standart butonlar (OK, Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept) # OK tıklandığında accept() çağırır
        self.button_box.rejected.connect(self.reject) # Cancel tıklandığında reject() çağırır
        layout.addRow(self.button_box)

    def get_settings(self):
        """Kullanıcının girdiği ayarları bir dictionary olarak döndürür."""
        return {
            "front": self.front_input.text(),
            "back": self.back_input.text(),
            "top": self.top_input.text(),
            "iso": self.isometric_input.text(),
        }

# -----------------------------------------------------------------------------
# Ana Pencere
# -----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FEA Uygulaması MVP")
        self.setGeometry(100, 100, 900, 700) # Biraz büyüttüm

        # Başlangıç Kamera Ayarları
        self.camera_settings = {
            "front": "0,0,-1",
            "back": "0,0,1",
            "top": "0,1,0",
            "iso": "iso"
        }

        # --- Menü Çubuğu Oluşturma ---
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Dosya")
        view_menu = menubar.addMenu("&Görünüm") # Yeni Görünüm Menüsü

        # "Aç..." eylemi
        open_action = QAction("&Aç...", self)
        open_action.setStatusTip("Bir mesh dosyası aç (.STL, .VTK vb.)")
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)

        file_menu.addSeparator() # Ayırıcı

        # "Kamera Ayarları..." eylemi
        camera_settings_action = QAction("&Kamera Ayarları...", self)
        camera_settings_action.setStatusTip("Kamera görünüm ayarlarını düzenle")
        camera_settings_action.triggered.connect(self.open_camera_settings_dialog)
        view_menu.addAction(camera_settings_action) # Görünüm menüsüne ekle

        file_menu.addSeparator() # Ayırıcı

        # "Çıkış" eylemi
        exit_action = QAction("&Çıkış", self)
        exit_action.setStatusTip("Uygulamadan çık")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # --- Menü Çubuğu Sonu ---

        # Durum Çubuğu
        self.statusBar().showMessage("Hazır")

        # Merkezi bir widget ve ana layout (Artık TabWidget yok)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # Ana dikey layout

        # Kamera Kontrol Butonları için yatay layout
        camera_buttons_layout = QHBoxLayout()
        
        btn_view_front = QPushButton("Ön")
        btn_view_front.clicked.connect(self.view_front)
        camera_buttons_layout.addWidget(btn_view_front)

        btn_view_back = QPushButton("Arka")
        btn_view_back.clicked.connect(self.view_back)
        camera_buttons_layout.addWidget(btn_view_back)

        btn_view_top = QPushButton("Üst")
        btn_view_top.clicked.connect(self.view_top)
        camera_buttons_layout.addWidget(btn_view_top)

        btn_view_isometric = QPushButton("İzometrik")
        btn_view_isometric.clicked.connect(self.view_isometric)
        camera_buttons_layout.addWidget(btn_view_isometric)

        btn_reset_camera = QPushButton("Kamerayı Sıfırla")
        btn_reset_camera.clicked.connect(self.reset_camera)
        camera_buttons_layout.addWidget(btn_reset_camera)

        main_layout.addLayout(camera_buttons_layout) # Butonları ana layout'a ekle

        # PyVista Plotter (render alanı)
        self.plotter = QtInteractor(central_widget) # Parent olarak central_widget
        main_layout.addWidget(self.plotter.interactor, 1) # 1 stretch faktörü ile plotter'a daha fazla yer ver

        # Başlangıçta sahne
        self.plotter.add_axes()
        self.plotter.camera_position = self.camera_settings["iso"]
        self.plotter.reset_camera()

    @Slot()
    def open_camera_settings_dialog(self):
        dialog = CameraSettingsDialog(self, current_settings=self.camera_settings)
        if dialog.exec(): # exec() diyalog kapanana kadar bekler, OK ise True döner
            self.camera_settings = dialog.get_settings()
            self.statusBar().showMessage("Kamera ayarları güncellendi.")
            # İsteğe bağlı: Ayarlar güncellendikten sonra bir görünümü tetikleyebilirsiniz
            # self.view_isometric() 
            QMessageBox.information(self, "Başarılı", "Kamera ayarları kaydedildi!")
        else:
            self.statusBar().showMessage("Kamera ayarları değiştirilmedi.")

    @Slot()
    def open_file_dialog(self):
        self.statusBar().showMessage("Dosya seçiliyor...")
        file_filter = "Mesh Dosyaları (*.stl *.vtk *.vtu *.ply *.obj);;STL Dosyaları (*.stl);;VTK Dosyaları (*.vtk);;Tüm Dosyalar (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(self,"Mesh Dosyası Aç","",file_filter)

        if file_path:
            self.statusBar().showMessage(f"{file_path} yükleniyor...")
            self.load_mesh(file_path)
        else:
            self.statusBar().showMessage("Dosya seçimi iptal edildi.")

    def load_mesh(self, file_path):
        try:
            mesh = pv.read(file_path)
            self.plotter.clear_actors()
            self.plotter.add_mesh(mesh, show_edges=True, name="main_mesh", color="lightblue")
            self.reset_camera()
            self.statusBar().showMessage(f"{file_path} başarıyla yüklendi.")
            print(f"Yüklenen mesh bilgisi: {mesh}")
        except Exception as e:
            self.statusBar().showMessage(f"Hata: Mesh yüklenemedi - {e}")
            QMessageBox.critical(self, "Yükleme Hatası", f"Mesh dosyası yüklenirken bir hata oluştu:\n{e}")
            print(f"Hata: {e}")

    def _parse_vector_str(self, vector_str):
        try:
            return tuple(map(float, vector_str.split(',')))
        except ValueError:
            QMessageBox.warning(self, "Format Hatası", f"'{vector_str}' geçerli bir vektör formatı değil (örn: x,y,z).")
            return None

    def view_front(self):
        vector = self._parse_vector_str(self.camera_settings["front"])
        if vector:
            self.plotter.view_vector(vector, viewup=[0,1,0])
            self.statusBar().showMessage("Ön görünüm uygulandı.")

    def view_back(self):
        vector = self._parse_vector_str(self.camera_settings["back"])
        if vector:
            self.plotter.view_vector(vector, viewup=[0,1,0])
            self.statusBar().showMessage("Arka görünüm uygulandı.")

    def view_top(self):
        vector = self._parse_vector_str(self.camera_settings["top"])
        if vector:
             # Üstten bakışta genellikle Z ekseni yukarı bakar (CAD programlarında)
             # veya Y ekseni. PyVista'da view_vector ile bakış yönünü,
             # viewup ile de kameranın "üst" yönünü belirlersiniz.
             # Eğer modeliniz XY düzlemindeyse ve Z derinlikse, üstten bakış için:
             # Bakış yönü: (0,0,1) (pozitif Z'den) veya (0,0,-1) (negatif Z'den)
             # View up: (0,1,0) (Y ekseni yukarı)
            self.plotter.view_vector(vector, viewup=[0,0,1]) # Eğer Z yukarıysa (matematiksel koordinatlar)
            # self.plotter.view_vector(vector, viewup=[0,1,0]) # Eğer Y yukarıysa (bazı modellemeler)
            # Doğru viewup modelinizin oryantasyonuna bağlı olacaktır.
            self.statusBar().showMessage("Üst görünüm uygulandı.")

    def view_isometric(self):
        iso_setting = self.camera_settings["iso"]
        if iso_setting.lower() == "iso":
            self.plotter.view_isometric()
        else:
            try:
                if len(iso_setting.split(',')) == 3 and ';' not in iso_setting:
                     pos = self._parse_vector_str(iso_setting)
                     if pos:
                         self.plotter.camera_position = [pos, self.plotter.camera.focal_point, self.plotter.camera.up]
                else:
                    self.plotter.camera_position = iso_setting
                self.statusBar().showMessage("İzometrik/Özel görünüm uygulandı.")
            except Exception as e:
                QMessageBox.warning(self, "Format Hatası", f"İzometrik kamera pozisyonu formatı hatalı: {e}")

    def reset_camera(self):
        if self.plotter.renderer.actors:
            self.plotter.reset_camera()
            self.statusBar().showMessage("Kamera sıfırlandı.")
        else:
            self.statusBar().showMessage("Sahnede gösterilecek bir model yok.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())