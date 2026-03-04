import sys
import os
import platform
from pathlib import Path
import pyttsx3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QComboBox,
    QCheckBox, QPushButton, QFileDialog, QProgressBar, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer


class TTSWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, text, voice_name, filepath, play_after, rate=170):
        super().__init__()
        self.text = text
        self.voice_name = voice_name
        self.filepath = Path(filepath)
        self.play_after = play_after
        self.rate = rate

    def run(self):
        try:
            self.progress.emit("Initializing TTS engine...")
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            
            # Pronađi glas (bez razlikovanja velikih i malih slova radi boljeg podudaranja)
            voice_found = False
            for voice in voices:
                if self.voice_name and self.voice_name.casefold() in voice.name.casefold():
                    engine.setProperty("voice", voice.id)
                    voice_found = True
                    break

            if not voice_found:
                if voices:
                    engine.setProperty("voice", voices[0].id)
                self.finished.emit(f"Voice '{self.voice_name}' not found. Using default.")
            
            # UPIŠI VREDNOSTI
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", 0.9)  # Dodata kontrola jačine zvuka
            
            self.progress.emit("Converting text to speech...")
            self.filepath.parent.mkdir(exist_ok=True)  # Uverite se da direktorijum postoji
            
            engine.save_to_file(self.text, str(self.filepath))
            engine.runAndWait()
            
            if self.play_after:
                self.progress.emit("Playing audio...")
                self._play_audio(str(self.filepath))
            
            self.finished.emit(f"✅ Saved to: {self.filepath.name}")
        except Exception as e:
            self.finished.emit(f"❌ Error: {str(e)}")

    def _play_audio(self, filepath):
        """Improved cross-platform audio playback"""
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            os.system(f"open '{filepath}'")
        else:  # Linux/Unix
            os.system(f"xdg-open '{filepath}'")


class TTSApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text to Audio Converter v2.0")
        self.setWindowIcon(QIcon("ico.ico"))
        self.setMinimumSize(650, 550)
        self.init_style()
        self.setup_ui()

    def init_style(self):
        """Centralized stylesheet with better theming"""
        self.setStyleSheet("""
            QWidget { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                font-family: 'Segoe UI', -apple-system, Arial, sans-serif;
            }
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #38bdf8, stop:1 #0ea5e9);
                color: white; border: none; 
                padding: 12px 24px; border-radius: 10px; 
                font-weight: 600; font-size: 14px;
            }
            QPushButton:hover { background: #0284c7; }
            QPushButton:pressed { background: #0369a1; }
            QPushButton:disabled { background: #94a3b8; }
            QTextEdit { 
                border: 2px solid #e2e8f0; 
                border-radius: 10px; 
                padding: 12px; 
                font-size: 14px;
                background: white;
            }
            QTextEdit:focus { border-color: #38bdf8; }
            QComboBox, QCheckBox { 
                border: 2px solid #e2e8f0; 
                border-radius: 8px; 
                padding: 8px; 
                font-size: 14px;
            }
            QProgressBar {
                border: 2px solid #e2e8f0; 
                border-radius: 8px; 
                text-align: center;
                background: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38bdf8, stop:1 #0ea5e9);
                border-radius: 6px;
            }
        """)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # HEADER
        header_layout = QVBoxLayout()
        title = QLabel("🎙️ Text to Audio Converter")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: 700; color: #1e293b; margin: 0;")
        
        subtitle = QLabel("Convert text to natural speech • Multiple voices • Auto-play")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 15px; color: #64748b; margin: 0;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # POLJPOLJE ZA TEKST
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "📝 Paste your text here...\n"
            "• Supports multiple paragraphs\n"
            "• Up to 5000 characters recommended\n"
            "• Works with any language your system supports"
        )
        self.text_input.setMaximumHeight(220)
        self.text_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_input)

        # KONTROLA REDOVA
        controls_layout = QHBoxLayout()
        
        # BIRANJE GLASA
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("🎤 Voice:"))
        self.voice_dropdown = QComboBox()
        self.voice_dropdown.setMinimumWidth(200)
        voice_layout.addWidget(self.voice_dropdown)
        voice_layout.addStretch()
        controls_layout.addLayout(voice_layout)

        # Klizač za brzinu bi bio ovde (buduće poboljšanje)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # OPCIJE
        options_layout = QHBoxLayout()
        self.play_checkbox = QCheckBox("🔊 Play automatically after saving")
        self.play_checkbox.setChecked(True)
        options_layout.addWidget(self.play_checkbox)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # DUGMAD
        btn_layout = QHBoxLayout()
        self.convert_btn = QPushButton("🎵 Convert to Audio")
        self.convert_btn.clicked.connect(self.convert_audio)
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        
        btn_layout.addWidget(self.convert_btn, 1)
        btn_layout.addWidget(self.clear_btn, 0)
        layout.addLayout(btn_layout)

        # Progress
        self.progress_label = QLabel("✅ Ready to convert")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; padding: 10px; color: #059669;")
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress)

        # Footer
        footer = QLabel("Software created by Šamec Uglješa © 2026")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(footer)

        self.setLayout(layout)
        self.populate_voices()
        self.char_count_timer = QTimer()
        self.char_count_timer.setSingleShot(True)
        self.char_count_timer.timeout.connect(self._update_char_count)

    def _on_text_changed(self):
        """Update character count display"""
        self.char_count_timer.start(500)  # Debounce

    def _update_char_count(self):
        count = len(self.text_input.toPlainText())
        # Može se dodati broj znakova u rezervisano mesto ili status

    def populate_voices(self):
        """Enhanced voice population with better error handling"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.stop()
            
            self.voices = voices or []
            self.voice_dropdown.clear()
            
            if voices:
                for voice in voices:
                    display_name = f"{voice.name} ({voice.languages[0] if voice.languages else 'en'})"
                    self.voice_dropdown.addItem(display_name, voice.name)
            else:
                self.voice_dropdown.addItem("No voices available")
                
        except Exception as e:
            self.voice_dropdown.addItem("Default Voice")
            print(f"Voice detection error: {e}")

    def clear_all(self):
        """Clear text and reset UI"""
        self.text_input.clear()
        self.progress_label.setText("✅ Ready to convert")
        self.progress.setVisible(False)

    def convert_audio(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "⚠️ No Text", "Please enter some text first!")
            return

        if len(text) > 10000:
            QMessageBox.warning(self, "⚠️ Text Too Long", 
                              "Text is too long (max 10k chars). Please shorten it.")
            return

        # Podrazumevano ime datoteke
        default_name = f"speech_{int(os.times()[4]*1000):.0f}.wav"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Audio File", default_name,
            "WAV files (*.wav);;MP3 files (*.mp3);;All files (*.*)"
        )
        if not filepath:
            return

        # Obezbedite ekstenziju .wav
        if not filepath.lower().endswith('.wav'):
            filepath = Path(filepath).with_suffix('.wav')

        # Započni konverziju
        self.convert_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress_label.setText("🚀 Starting conversion...")

        self.worker = TTSWorker(
            text, self.voice_dropdown.currentData() or self.voice_dropdown.currentText(),
            filepath, self.play_checkbox.isChecked()
        )
        self.worker.progress.connect(self.progress_label.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, msg):
        self.progress.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        if "✅" in msg:
            self.progress_label.setStyleSheet("font-size: 14px; padding: 10px; color: #059669;")
            QMessageBox.information(self, "🎉 Success!", msg)
        else:
            self.progress_label.setStyleSheet("font-size: 14px; padding: 10px; color: #dc2626;")
            QMessageBox.critical(self, "❌ Conversion Failed", msg)
        
        self.progress_label.setText("✅ Ready to convert")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = TTSApp()
    window.show()
    sys.exit(app.exec_())
