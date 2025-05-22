# main.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox,
    QLabel, QInputDialog, QHBoxLayout, QPushButton, QLineEdit # QLineEdit eklenmişti
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Slot, Qt
import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FEA Uygulaması MVP")
        self.setGeometry(100, 100, 1000, 750)

        # Veri saklama
        self.material_properties = {"E": None, "nu": None}
        self.fixed_nodes_indices = []
        self.applied_forces = {}
        self.current_mesh = None
        self.selected_point_actor = None
        self.fixed_nodes_actor = None
        self.force_arrows_actor = None
        self.last_picked_point_coords = None
        self.last_picked_node_index = None

        # --- Menü Çubuğu ---
        menubar = self.menuBar()

        # Dosya Menüsü
        file_menu = menubar.addMenu("&Dosya")
        open_action = QAction(QIcon.fromTheme("document-open", QIcon(":/qt-project.org/styles/commonstyle/images/standardbutton-open-32.png")), "&Aç...", self)
        open_action.setStatusTip("Bir mesh dosyası aç (.STL, .VTK vb.)")
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction(QIcon.fromTheme("application-exit"), "&Çıkış", self)
        exit_action.setStatusTip("Uygulamadan çık")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Görünüm Menüsü
        view_menu = menubar.addMenu("&Görünüm")
        front_action = QAction("Ön Görünüm", self)
        front_action.triggered.connect(self.view_front)
        view_menu.addAction(front_action)
        top_action = QAction("Üst Görünüm", self)
        top_action.triggered.connect(self.view_top)
        view_menu.addAction(top_action)
        right_action = QAction("Sağ Görünüm", self)
        right_action.triggered.connect(self.view_right)
        view_menu.addAction(right_action)
        isometric_action = QAction("İzometrik Görünüm", self)
        isometric_action.triggered.connect(self.view_isometric)
        view_menu.addAction(isometric_action)
        view_menu.addSeparator()
        reset_cam_action = QAction("Kamerayı Sıfırla (Mesh'e)", self)
        reset_cam_action.triggered.connect(self.reset_camera_for_mesh)
        view_menu.addAction(reset_cam_action)
        view_menu.addSeparator()
        self.box_zoom_action = QAction("Kutu Zoom Modu", self, checkable=True)
        self.box_zoom_action.setStatusTip("Kutu çizerek zoom yapma modunu etkinleştir/devre dışı bırak (genellikle 'b' tuşu ile)")
        self.box_zoom_action.triggered.connect(self.toggle_box_zoom_mode)
        view_menu.addAction(self.box_zoom_action)

        # Analiz Ayarları Menüsü
        settings_menu = menubar.addMenu("&Analiz Ayarları")
        material_submenu = settings_menu.addMenu("Malzeme Özellikleri")
        youngs_action = QAction("Young Modülü (E) Gir", self)
        youngs_action.triggered.connect(lambda: self.get_material_property("E", "Young Modülü (E) Girin:", "Young Modülü (E):"))
        material_submenu.addAction(youngs_action)
        poisson_action = QAction("Poisson Oranı (ν) Gir", self)
        poisson_action.triggered.connect(lambda: self.get_material_property("nu", "Poisson Oranı (ν) Girin:", "Poisson Oranı (ν):"))
        material_submenu.addAction(poisson_action)
        settings_menu.addSeparator()
        bc_load_submenu = settings_menu.addMenu("Sınır Koşulları ve Yükler")
        self.select_mode_action = QAction("Düğüm Seç Modu", self, checkable=True)
        self.select_mode_action.setStatusTip("Düğüm seçme modunu etkinleştir/devre dışı bırak")
        self.select_mode_action.triggered.connect(self.toggle_select_mode)
        bc_load_submenu.addAction(self.select_mode_action)
        fix_node_action = QAction("Seçili Düğümü Sabitle", self)
        fix_node_action.triggered.connect(self.fix_selected_node_action)
        bc_load_submenu.addAction(fix_node_action)
        unfix_node_action = QAction("Seçili Düğümün Sabitlemesini Kaldır", self)
        unfix_node_action.triggered.connect(self.unfix_selected_node_action)
        bc_load_submenu.addAction(unfix_node_action)
        apply_force_action = QAction("Seçili Düğüm(ler)e Kuvvet Uygula...", self)
        apply_force_action.triggered.connect(self.apply_force_dialog)
        bc_load_submenu.addAction(apply_force_action)
        settings_menu.addSeparator()
        clear_bc_action = QAction("Tüm Sınır Koşullarını ve Yükleri Temizle", self)
        clear_bc_action.triggered.connect(self.clear_all_bcs_and_loads)
        settings_menu.addAction(clear_bc_action)

        # Durum Çubuğu
        self.statusBar().showMessage("Hazır")

        # Merkezi widget ve ana layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # PyVista render alanı
        self.plotter = QtInteractor(central_widget)
        main_layout.addWidget(self.plotter.interactor, 1)

        # Başlangıçta sahne
        self.plotter.add_axes()
        self.plotter.camera_position = 'iso'

    @Slot()
    def open_file_dialog(self):
        self.statusBar().showMessage("Dosya seçiliyor...")
        file_filter = "Mesh Dosyaları (*.stl *.vtk *.vtu *.ply *.obj);;Tüm Dosyalar (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Mesh Dosyası Aç", "", file_filter)
        if file_path:
            self.statusBar().showMessage(f"{file_path} yükleniyor...")
            self.load_mesh(file_path)
        else:
            self.statusBar().showMessage("Dosya seçimi iptal edildi.")

    def load_mesh(self, file_path):
        try:
            self.current_mesh = pv.read(file_path)
            if not self.current_mesh or not self.current_mesh.points.size:
                raise ValueError("Mesh dosyası geçerli noktalar içermiyor veya okunamadı.")
            self.plotter.clear_actors()
            self.plotter.add_mesh(self.current_mesh, name="main_mesh", show_edges=True, color="lightblue")
            self.reset_camera_for_mesh()
            self.statusBar().showMessage(f"{file_path} başarıyla yüklendi.")
            self.clear_all_bcs_and_loads(inform_user=False)
            self.last_picked_node_index = None
            self.last_picked_point_coords = None
            self.remove_selection_marker()
            if self.select_mode_action.isChecked():
                self.plotter.enable_point_picking(
                    callback=self.on_raw_point_picked,
                    show_message=False
                )
        except Exception as e:
            self.current_mesh = None
            self.statusBar().showMessage(f"Hata: Mesh yüklenemedi - {e}")
            QMessageBox.critical(self, "Yükleme Hatası", f"Mesh dosyası yüklenirken bir hata oluştu:\n{e}")
            print(f"Hata: {e}")

    def get_material_property(self, prop_key, title, label):
        current_val_str = str(self.material_properties.get(prop_key, "0.0"))
        text, ok = QInputDialog.getText(self, title, label, QLineEdit.Normal, current_val_str)
        if ok and text:
            try:
                value = float(text)
                self.material_properties[prop_key] = value
                self.statusBar().showMessage(f"{label.split(':')[0]} ayarlandı: {value}")
            except ValueError:
                QMessageBox.warning(self, "Geçersiz Değer", "Lütfen geçerli bir sayı girin.")

    @Slot(bool)
    def toggle_select_mode(self, checked):
        if not self.current_mesh:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir mesh dosyası yükleyin.")
            self.select_mode_action.setChecked(False)
            return
        if checked:
            self.statusBar().showMessage("Düğüm Seç Modu Aktif. Seçmek için bir düğüme tıklayın. Gezinmek için modu kapatın.")
            self.plotter.enable_point_picking(
                callback=self.on_raw_point_picked,
                show_message=False
            )
        else:
            self.statusBar().showMessage("Düğüm Seç Modu Devre Dışı. Normal gezinme aktif.")
            self.plotter.disable_picking()
            self.remove_selection_marker()

    def on_raw_point_picked(self, picked_3d_point_coords):
        print(f"DEBUG: on_raw_point_picked çağrıldı. Gelen 3D koordinat: {picked_3d_point_coords}")
        if not self.current_mesh or not hasattr(self.current_mesh, 'points'):
            return
        clicked_point = None
        if picked_3d_point_coords is not None:
            if isinstance(picked_3d_point_coords, (list, np.ndarray)):
                if len(picked_3d_point_coords) == 1 and isinstance(picked_3d_point_coords[0], (list, np.ndarray)) and len(picked_3d_point_coords[0]) == 3:
                    clicked_point = np.array(picked_3d_point_coords[0])
                elif len(picked_3d_point_coords) == 3 and all(isinstance(x, (int, float)) for x in picked_3d_point_coords):
                    clicked_point = np.array(picked_3d_point_coords)
        if clicked_point is not None:
            distances = np.linalg.norm(self.current_mesh.points - clicked_point, axis=1)
            node_index = np.argmin(distances)
            if distances[node_index] > (self.current_mesh.length * 0.1):
                print(f"DEBUG: En yakın düğüm çok uzak (mesafe: {distances[node_index]:.3f}). Seçim yapılmadı.")
                self.last_picked_node_index = None
                self.last_picked_point_coords = None
                self.remove_selection_marker()
                self.statusBar().showMessage("Mesh üzerinde bir düğüme yakın tıklayın.")
                return
            self.last_picked_point_coords = self.current_mesh.points[node_index].copy()
            self.last_picked_node_index = int(node_index)
            self.statusBar().showMessage(f"Düğüm {self.last_picked_node_index} seçildi ({self.last_picked_point_coords[0]:.2f}, {self.last_picked_point_coords[1]:.2f}, {self.last_picked_point_coords[2]:.2f}).")
            self.update_selection_marker()
        else:
            self.last_picked_node_index = None
            self.last_picked_point_coords = None
            self.remove_selection_marker()
            self.statusBar().showMessage("Düğüm seçimi kaldırıldı veya geçersiz tıklama.")

    def update_selection_marker(self):
        self.remove_selection_marker()
        if self.last_picked_point_coords is not None and self.current_mesh:
            bounds = self.current_mesh.bounds
            if not all(np.isfinite(bounds)): marker_radius = 0.01
            else:
                diag_length = np.sqrt((bounds[1]-bounds[0])**2 + (bounds[3]-bounds[2])**2 + (bounds[5]-bounds[4])**2)
                marker_radius = diag_length * 0.0075
                if marker_radius < 1e-6 : marker_radius = 0.01
            marker = pv.Sphere(center=self.last_picked_point_coords, radius=marker_radius)
            self.selected_point_actor = self.plotter.add_mesh(marker, color="yellow", name="selection_marker", pickable=False)

    def remove_selection_marker(self):
        if self.selected_point_actor:
            self.plotter.remove_actor(self.selected_point_actor, render=False)
            self.selected_point_actor = None
            self.plotter.render()

    def update_fixed_nodes_visualization(self):
        if self.fixed_nodes_actor:
            self.plotter.remove_actor(self.fixed_nodes_actor, render=False)
            self.fixed_nodes_actor = None
        if self.fixed_nodes_indices and self.current_mesh:
            points_to_mark = self.current_mesh.points[self.fixed_nodes_indices]
            if points_to_mark.size > 0:
                bounds = self.current_mesh.bounds
                if not all(np.isfinite(bounds)): marker_radius = 0.015
                else:
                    diag_length = np.sqrt((bounds[1]-bounds[0])**2 + (bounds[3]-bounds[2])**2 + (bounds[5]-bounds[4])**2)
                    marker_radius = diag_length * 0.01
                    if marker_radius < 1e-6 : marker_radius = 0.015
                cloud = pv.PolyData(points_to_mark)
                glyphs = cloud.glyph(geom=pv.Sphere(radius=marker_radius), scale=False, orient=False)
                self.fixed_nodes_actor = self.plotter.add_mesh(glyphs, color="red", name="fixed_nodes_markers", pickable=False)
        self.plotter.render()

    # ---- update_forces_visualization METODU GÜNCELLENDİ ----
    def update_forces_visualization(self):
        if self.force_arrows_actor:
            self.plotter.remove_actor(self.force_arrows_actor, render=False)
            self.force_arrows_actor = None

        if self.applied_forces and self.current_mesh:
            starts = []
            directions = []
            magnitudes = [] 

            for node_idx, force_vector_list in self.applied_forces.items():
                if 0 <= node_idx < len(self.current_mesh.points):
                    force_vector = np.array(force_vector_list)
                    force_mag = np.linalg.norm(force_vector)
                    if force_mag < 1e-9: # Çok küçük kuvvetleri gösterme
                        continue
                    starts.append(self.current_mesh.points[node_idx])
                    directions.append(force_vector / force_mag) # Normalize et
                    magnitudes.append(force_mag)

            if starts:
                points_pd = pv.PolyData(np.array(starts))
                points_pd['vectors'] = np.array(directions) 
                points_pd['magnitudes'] = np.array(magnitudes)

                bounds = self.current_mesh.bounds
                if not all(np.isfinite(bounds)):
                    base_shaft_radius = 0.005
                    base_tip_length = 0.02
                    base_tip_radius = 0.01
                    scale_factor = 0.1 
                else:
                    diag_length = np.sqrt((bounds[1]-bounds[0])**2 + (bounds[3]-bounds[2])**2 + (bounds[5]-bounds[4])**2)
                    base_shaft_radius = diag_length * 0.0025
                    base_tip_length = diag_length * 0.01
                    base_tip_radius = diag_length * 0.005
                    
                    max_mag = np.max(magnitudes) if magnitudes else 1.0
                    if max_mag < 1e-6: max_mag = 1.0
                    scale_factor = (diag_length * 0.05) / max_mag

                arrow_prototype = pv.Arrow(
                    direction=[0,0,1], 
                    shaft_radius=base_shaft_radius,
                    tip_length=base_tip_length,
                    tip_radius=base_tip_radius
                )
                
                glyphs = points_pd.glyph(
                    orient='vectors',      
                    scale='magnitudes',    
                    factor=scale_factor,   
                    geom=arrow_prototype,  
                )

                if glyphs.n_points > 0: 
                    self.force_arrows_actor = self.plotter.add_mesh(glyphs, color="blue", name="force_arrows", pickable=False)
                else:
                    print("DEBUG: Kuvvetler için glif oluşturulamadı.")
        
        self.plotter.render()
    # ---- GÜNCELLENEN METOD SONU ----

    @Slot()
    def fix_selected_node_action(self):
        if self.last_picked_node_index is None:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce sabitlemek için bir düğüm seçin.")
            return
        if self.last_picked_node_index not in self.fixed_nodes_indices:
            self.fixed_nodes_indices.append(self.last_picked_node_index)
            self.fixed_nodes_indices.sort()
            self.statusBar().showMessage(f"Düğüm {self.last_picked_node_index} sabitlendi.")
            self.update_fixed_nodes_visualization()
        else:
            self.statusBar().showMessage(f"Düğüm {self.last_picked_node_index} zaten sabitlenmiş.")
            
    @Slot()
    def unfix_selected_node_action(self):
        if self.last_picked_node_index is None:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce sabitlemesini kaldırmak için bir düğüm seçin.")
            return
        if self.last_picked_node_index in self.fixed_nodes_indices:
            self.fixed_nodes_indices.remove(self.last_picked_node_index)
            self.statusBar().showMessage(f"Düğüm {self.last_picked_node_index} sabitlemesi kaldırıldı.")
            self.update_fixed_nodes_visualization()
        else:
            self.statusBar().showMessage(f"Düğüm {self.last_picked_node_index} zaten sabit değil.")

    @Slot()
    def apply_force_dialog(self):
        if self.last_picked_node_index is None:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce kuvvet uygulamak için bir düğüm seçin.")
            return
        node_idx = self.last_picked_node_index
        current_force_str = [str(f) for f in self.applied_forces.get(node_idx, [0.0, 0.0, 0.0])]
        fx_str, ok_fx = QInputDialog.getText(self, f"Kuvvet Uygula (Düğüm {node_idx})", "Fx:", QLineEdit.Normal, current_force_str[0])
        if not ok_fx: return
        fy_str, ok_fy = QInputDialog.getText(self, f"Kuvvet Uygula (Düğüm {node_idx})", "Fy:", QLineEdit.Normal, current_force_str[1])
        if not ok_fy: return
        fz_str, ok_fz = QInputDialog.getText(self, f"Kuvvet Uygula (Düğüm {node_idx})", "Fz:", QLineEdit.Normal, current_force_str[2])
        if not ok_fz: return
        try:
            fx, fy, fz = float(fx_str), float(fy_str), float(fz_str)
            if abs(fx) < 1e-9 and abs(fy) < 1e-9 and abs(fz) < 1e-9:
                if node_idx in self.applied_forces: del self.applied_forces[node_idx]
                self.statusBar().showMessage(f"Düğüm {node_idx} üzerindeki kuvvet kaldırıldı.")
            else:
                self.applied_forces[node_idx] = [fx, fy, fz]
                self.statusBar().showMessage(f"Düğüm {node_idx}'e kuvvet uygulandı: [{fx:.2f}, {fy:.2f}, {fz:.2f}]")
            self.update_forces_visualization()
        except ValueError:
            QMessageBox.warning(self, "Geçersiz Değer", "Lütfen kuvvet bileşenleri için geçerli sayılar girin.")
        
    @Slot()
    def clear_all_bcs_and_loads(self, inform_user=True):
        self.fixed_nodes_indices.clear()
        self.applied_forces.clear()
        if self.fixed_nodes_actor: self.plotter.remove_actor(self.fixed_nodes_actor, render=False); self.fixed_nodes_actor = None
        if self.force_arrows_actor: self.plotter.remove_actor(self.force_arrows_actor, render=False); self.force_arrows_actor = None
        self.plotter.render()
        if inform_user:
            self.statusBar().showMessage("Tüm sınır koşulları ve yükler temizlendi.")
            QMessageBox.information(self, "Temizlendi", "Tüm sınır koşulları ve yükler temizlendi.")

    @Slot(bool)
    def toggle_box_zoom_mode(self, checked):
        if not self.plotter or not self.plotter.iren: return
        if checked:
            self.plotter.enable_zoom_style()
            self.statusBar().showMessage("Kutu Zoom Modu Aktif. 'b' tuşuna basıp kutu çizebilirsiniz.")
            QMessageBox.information(self, "Kutu Zoom Modu", 
                                    "Kutu Zoom Modu etkinleştirildi.\n"
                                    "Plotter üzerinde 'b' tuşuna basarak bir kutu çizebilir ve o alana zoom yapabilirsiniz.\n"
                                    "(Bu mod, 'r' tuşu ile lastik bant zoom'u da etkinleştirebilir.)")
        else:
            try:
                # VTK import et (eğer PyVista içinden direkt erişim yoksa)
                import vtk
                # Standart TrackballCamera interactor stilini oluştur
                style = vtk.vtkInteractorStyleTrackballCamera()
                # Plotter'ın interactor'ına bu stili ata
                if hasattr(self.plotter.iren, 'SetInteractorStyle'): #iren, vtkRenderWindowInteractor olmalı
                    self.plotter.iren.SetInteractorStyle(style)
                else: # Bazen plotter.interactor doğrudan stil olabilir
                    self.plotter.interactor.SetInteractorStyle(style)

            except ImportError:
                print("VTK import edilemedi, interactor stili manuel olarak değiştirilemiyor.")
                QMessageBox.warning(self, "Hata", "Kutu zoom modu kapatılamadı (VTK sorunu).")
            except AttributeError as e:
                print(f"Interactor stili ayarlanamadı: {e}")
                QMessageBox.warning(self, "Hata", f"Kutu zoom modu kapatılamadı (Interactor sorunu): {e}")


            self.statusBar().showMessage("Kutu Zoom Modu Devre Dışı. Normal zoom/gezinme aktif.")
            QMessageBox.information(self, "Kutu Zoom Modu", "Kutu Zoom Modu devre dışı bırakıldı.")

    # Kamera Kontrolleri
    def view_front(self):
        if self.current_mesh: self.plotter.view_vector((0,0,-1), viewup=(0,1,0))
    def view_top(self):
        if self.current_mesh: self.plotter.view_vector((0,1,0), viewup=(0,0,-1))
    def view_right(self):
        if self.current_mesh: self.plotter.view_vector((1,0,0), viewup=(0,1,0))
    def view_isometric(self):
        if self.current_mesh: self.plotter.view_isometric()
    def reset_camera_for_mesh(self):
        if self.current_mesh: self.plotter.reset_camera()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())