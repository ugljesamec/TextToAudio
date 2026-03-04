import sys
import os
import platform
import pyttsx3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QComboBox,
    QCheckBox, QPushButton, QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# TTS THREAD 
class TTSWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, text, voice_name, filepath, play_after):
        super().__init__()
        self.text = text
        self.voice_name = voice_name
        self.filepath = filepath
        self.play_after = play_after

    def run(self):
        try:
            engine = pyttsx3.init()
            for v in engine.getProperty("voices"):
                if v.name == self.voice_name:
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate", 170)
            engine.save_to_file(self.text, self.filepath)
            engine.runAndWait()

            if self.play_after:
                if platform.system() == "Windows":
                    os.startfile(self.filepath)
                elif platform.system() == "Darwin":
                    os.system(f"open {self.filepath}")
                else:
                    os.system(f"xdg-open {self.filepath}")

            self.finished.emit("Success")
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

# APLIKACIJA
class TTSApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text to Audio")
        # PUTANJA IKONE
        self.setWindowIcon(QIcon("ico.ico"))  # <-- PUTANJA
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # NASLOV
        self.title_label = QLabel("Text to Audio")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(self.title_label)

        # SUBNASLOV
        self.subtitle_label = QLabel("Paste text below, choose a voice, and convert it into audio.")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label)

        # POLJE ZA TEKST
        self.text_input = QTextEdit()
        layout.addWidget(self.text_input)

        # DROPDOWN ZA GLAS
        self.voice_dropdown = QComboBox()
        engine = pyttsx3.init()
        self.voices = engine.getProperty("voices")
        engine.stop()
        for v in self.voices:
            self.voice_dropdown.addItem(v.name)
        layout.addWidget(self.voice_dropdown)

        # Polje za potvrdu Pusti posle čuvanja
        self.play_checkbox = QCheckBox("Play audio after save")
        self.play_checkbox.setChecked(True)
        layout.addWidget(self.play_checkbox)

        # DUGMAD
        self.convert_btn = QPushButton("Convert to Audio")
        self.convert_btn.clicked.connect(self.convert_audio)
        self.clear_btn = QPushButton("Clear Text")
        self.clear_btn.clicked.connect(lambda: self.text_input.clear())
        self.quit_btn = QPushButton("Quit App")
        self.quit_btn.clicked.connect(self.close)

        layout.addWidget(self.convert_btn)
        layout.addWidget(self.clear_btn)
        layout.addWidget(self.quit_btn)

        # Traka napretka
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # FOOTER
        self.footer_label = QLabel("Software created by Šamec Uglješa © 2025")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setStyleSheet("font-size: 10px; color: gray;")
        layout.addWidget(self.footer_label)

        self.setLayout(layout)

    def convert_audio(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter some text!")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Save Audio File", "", "WAV files (*.wav)")
        if not filepath:
            return

        self.progress.setVisible(True)
        self.convert_btn.setEnabled(False)

        # POKRETANJE TTS u thread-u
        self.thread = TTSWorker(
            text,
            self.voice_dropdown.currentText(),
            filepath,
            self.play_checkbox.isChecked()
        )
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, msg):
        self.progress.setVisible(False)
        self.convert_btn.setEnabled(True)
        if msg == "Success":
            QMessageBox.information(self, "Done", "Audio file created successfully!")
        else:
            QMessageBox.critical(self, "Error", msg)

#  POKRETANJE APP 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TTSApp()
    window.show()
    sys.exit(app.exec())