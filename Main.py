import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMenuBar, QAction,
    QStatusBar, QFileDialog, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
import sqlite3
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

class DecisionSupportSystem(QMainWindow):
    def __init__(self, Nama="Maftuh Ahnan Al-Kautsar", NIM="F1D022135"):
        super().__init__()
        self.setWindowTitle("SPK Pemilihan Mobil Operasional Terbaik - Metode SAW")
        self.setGeometry(100, 100, 1000, 700)
        self.selected_row = None  # Untuk menyimpan baris yang dipilih

        # Menu Bar
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        file_menu = menubar.addMenu("File")
        file_menu.addAction(QAction("Export Hasil SAW ke PDF", self, triggered=self.export_to_pdf))
        file_menu.addAction(QAction("Export Data Mobil ke CSV", self, triggered=self.export_to_csv))
        file_menu.addAction(QAction("Exit", self, triggered=self.close))

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(QAction("About", self, triggered=self.show_help))

        # Central Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Input Panel
        input_group = QGroupBox("Input Data Mobil")
        form_layout = QGridLayout(input_group)
        labels = ["Nama Mobil", "Kapasitas", "Penampilan", "Merk", "Bahan Bakar", "Tipe", "Harga (Rp)"]
        self.inputs = []

        for i, label in enumerate(labels):
            form_layout.addWidget(QLabel(label + ":"), i, 0)
            line_edit = QLineEdit()
            self.inputs.append(line_edit)
            form_layout.addWidget(line_edit, i, 1)

        self.name_input, self.capacity_input, self.appearance_input, self.brand_input, \
            self.fuel_input, self.type_input, self.price_input = self.inputs

        # Button Layout
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Tambah ke Tabel")
        self.add_button.clicked.connect(self.add_to_table)
        button_layout.addWidget(self.add_button)

        form_layout.addLayout(button_layout, len(labels), 1)
        main_layout.addWidget(input_group, 2)

        # Table and Result Panel
        right_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Nama Mobil", "Kapasitas", "Penampilan", "Merk", "Bahan Bakar", "Tipe", "Harga"])
        self.table.setEditTriggers(QTableWidget.DoubleClicked)  # Aktifkan edit dengan double-click
        self.table.cellChanged.connect(self.update_cell_data)  # Tangani perubahan sel
        right_layout.addWidget(QLabel("Data Mobil"))
        right_layout.addWidget(self.table)

        self.calculate_button = QPushButton("Hitung SAW")
        self.calculate_button.clicked.connect(self.calculate_saw)
        right_layout.addWidget(self.calculate_button)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Rank", "Nama Mobil", "Hasil SAW"])
        right_layout.addWidget(QLabel("Hasil Perhitungan SAW"))
        right_layout.addWidget(self.result_table)

        self.delete_button = QPushButton("Hapus Data")
        self.delete_button.clicked.connect(self.delete_data)
        right_layout.addWidget(self.delete_button)

        main_layout.addLayout(right_layout, 5)

        # Status Bar
        status_bar = QStatusBar()
        status_bar.showMessage(f"Nama: {Nama} | NIM: {NIM}")
        self.setStatusBar(status_bar)

        # Styling dan penyesuaian ukuran tabel
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9f9f9;
            }
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }
            QLabel {
                font-size: 12px;
                color: #333;
            }
            QLineEdit {
                font-size: 12px;
                padding: 3px 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QPushButton#AddButton {
                background-color: #2ecc71;
                color: white;
                padding: 6px 14px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton#AddButton:hover {
                background-color: #27ae60;
            }
            QPushButton#DeleteButton {
                background-color: #e74c3c;
                color: white;
                padding: 6px 14px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton#DeleteButton:hover {
                background-color: #c0392b;
            }
            QPushButton#CalculateButton {
                background-color: #f1c40f;
                color: white;
                padding: 6px 14px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton#CalculateButton:hover {
                background-color: #d4ac0d;
            }
            QTableWidget {
                font-size: 12px;
                border: 1px solid #ccc;
                background-color: #ffffff;
            }
            QTableWidget#DataMobilTable {
                width: 100%;
            }
            QTableWidget#HasilSAWTable {
                width: 100%;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #ccc;
            }
        """)

        # Set object names for tables to apply specific styles
        self.table.setObjectName("DataMobilTable")
        self.result_table.setObjectName("HasilSAWTable")

        # Set object names for buttons to apply specific styles
        self.add_button.setObjectName("AddButton")
        self.delete_button.setObjectName("DeleteButton")
        self.calculate_button.setObjectName("CalculateButton")

        # Penyesuaian ukuran kolom secara otomatis
        self.table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setStretchLastSection(True)

        # Database Setup
        self.conn = sqlite3.connect("mobil_operasional.db")
        self.create_table()
        self.load_table_data()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                capacity REAL,
                appearance REAL,
                brand REAL,
                fuel_efficiency REAL,
                type REAL,
                price REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saw_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank INTEGER,
                name TEXT,
                score REAL
            )
        """)
        self.conn.commit()

    def load_table_data(self):
        self.table.setRowCount(0)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, capacity, appearance, brand, fuel_efficiency, type, price FROM candidates")
        data = cursor.fetchall()

        for row_data in data:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            # Simpan ID di item pertama (kolom nama) dengan Qt.UserRole
            item = QTableWidgetItem(str(row_data[1]))
            item.setData(Qt.UserRole, row_data[0])
            self.table.setItem(row_position, 0, item)
            for i, value in enumerate(row_data[2:], start=1):  # Mulai dari index 2 untuk skip ID dan nama
                self.table.setItem(row_position, i, QTableWidgetItem(str(value)))

        # Load SAW results into result_table
        self.result_table.setRowCount(0)
        cursor.execute("SELECT rank, name, score FROM saw_results ORDER BY rank")
        results = cursor.fetchall()
        for row_data in results:
            row_position = self.result_table.rowCount()
            self.result_table.insertRow(row_position)
            for i, value in enumerate(row_data):
                self.result_table.setItem(row_position, i, QTableWidgetItem(str(value)))

    def add_to_table(self):
        name = self.name_input.text().strip()
        if not name or any(field.text().strip() == '' for field in self.inputs[1:]):
            QMessageBox.warning(self, "Input Tidak Lengkap", "Harap isi semua kolom sebelum menambahkan ke tabel.")
            return

        try:
            values = [float(field.text()) for field in self.inputs[1:]]
        except ValueError:
            QMessageBox.warning(self, "Input Tidak Valid", "Mohon masukkan angka yang valid di kolom numerik.")
            return

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO candidates (name, capacity, appearance, brand, fuel_efficiency, type, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (name, *values))
        self.conn.commit()

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        cursor.execute("SELECT last_insert_rowid()")
        new_id = cursor.fetchone()[0]
        # Simpan ID di item pertama (kolom nama) dengan Qt.UserRole
        item = QTableWidgetItem(name)
        item.setData(Qt.UserRole, new_id)
        self.table.setItem(row_position, 0, item)
        for i, value in enumerate(values, start=1):
            self.table.setItem(row_position, i, QTableWidgetItem(str(value)))
        self.clear_inputs()
        self.selected_row = None

    def update_cell_data(self, row, column):
        item = self.table.item(row, column)
        if not item:
            return

        # Ambil ID dari item di kolom pertama (nama)
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        row_id = name_item.data(Qt.UserRole)
        value = item.text()
        columns = ['name', 'capacity', 'appearance', 'brand', 'fuel_efficiency', 'type', 'price']
        column_name = columns[column]

        # Validasi untuk kolom numerik
        if column_name != 'name':
            try:
                value = float(value)
            except ValueError:
                QMessageBox.warning(self, "Input Tidak Valid", f"Kolom {columns[column]} harus berupa angka.")
                self.load_table_data()  # Kembalikan data asli
                return

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE candidates SET {column_name} = ? WHERE id = ?", (value, row_id))
        self.conn.commit()

    def delete_data(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Pilih Data", "Silakan pilih data dari tabel untuk dihapus.")
            return

        row = selected_items[0].row()
        # Ambil ID dari item di kolom pertama (nama)
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        row_id = name_item.data(Qt.UserRole)

        reply = QMessageBox.question(self, 'Konfirmasi Hapus',
                                   'Apakah Anda yakin ingin menghapus data ini?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM candidates WHERE id = ?", (row_id,))
            cursor.execute("DELETE FROM saw_results WHERE name = (SELECT name FROM candidates WHERE id = ?)", (row_id,))
            self.conn.commit()
            self.table.removeRow(row)
            self.clear_inputs()
            self.selected_row = None
            self.load_table_data()  # Refresh result table

    def clear_inputs(self):
        for field in self.inputs:
            field.clear()

    def calculate_saw(self):
        self.result_table.setRowCount(0)
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, capacity, appearance, brand, fuel_efficiency, type, price FROM candidates")
        data = cursor.fetchall()

        if not data:
            QMessageBox.warning(self, "Tabel Kosong", "Belum ada data dalam tabel. Silakan tambahkan data terlebih dahulu.")
            return

        weights = [0.1837, 0.1633, 0.1429, 0.1837, 0.1429, 0.1837]
        benefit = [True, True, True, True, True, False]

        normalized = []
        for row in data:
            normalized_row = []
            for i, value in enumerate(row[1:]):
                if benefit[i]:
                    max_value = max(d[i+1] for d in data)
                    normalized_row.append(value / max_value if max_value else 0)
                else:
                    min_value = min(d[i+1] for d in data)
                    normalized_row.append(min_value / value if value else 0)
            normalized.append(normalized_row)

        results = []
        for i, norm_row in enumerate(normalized):
            weighted_sum = sum(norm * weight for norm, weight in zip(norm_row, weights))
            results.append((data[i][0], weighted_sum))

        results.sort(key=lambda x: x[1], reverse=True)

        # Clear previous SAW results
        cursor.execute("DELETE FROM saw_results")
        self.conn.commit()

        # Save new SAW results to database
        for i, (name, score) in enumerate(results, 1):
            cursor.execute("INSERT INTO saw_results (rank, name, score) VALUES (?, ?, ?)", (i, name, score))
            self.result_table.insertRow(i - 1)
            self.result_table.setItem(i - 1, 0, QTableWidgetItem(str(i)))
            self.result_table.setItem(i - 1, 1, QTableWidgetItem(name))
            self.result_table.setItem(i - 1, 2, QTableWidgetItem(f"{score:.2f}"))

        self.conn.commit()

    def export_to_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if file_path:
            pdf = SimpleDocTemplate(file_path, pagesize=letter)
            table_data = [["Rank", "Nama Mobil", "Hasil SAW"]]
            for i in range(self.result_table.rowCount()):
                row = [self.result_table.item(i, j).text() for j in range(3)]
                table_data.append(row)
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            pdf.build([table])

    def export_to_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            with open(file_path, "w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                headers = ["Nama Mobil", "Kapasitas", "Penampilan", "Merk", "Bahan Bakar", "Tipe", "Harga"]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                    writer.writerow(row_data)

    def show_help(self):
        QMessageBox.information(
            self,
            "Tentang Aplikasi",
            "Aplikasi SPK Pemilihan Mobil Operasional menggunakan metode SAW.\n"
            "Dibuat oleh: Maftuh Ahnan Al-Kautsar\nNIM: F1D022135\n\n"
            "Fitur:\n- Input data mobil\n- Edit langsung data di tabel\n- Hapus data mobil\n- Perhitungan SAW\n- Export PDF/CSV\n- Penyimpanan database SQLite"
        )

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"  # Enable automatic screen scaling
    app = QApplication(sys.argv)
    window = DecisionSupportSystem()
    window.show()
    sys.exit(app.exec_())