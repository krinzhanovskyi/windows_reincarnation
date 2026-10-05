def get_pocket_style(theme: str) -> str:
    if theme == "light":
        return """
            #PocketWindow {
                background-color: rgba(245, 245, 245, 245);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 25);
                font-family: 'Segoe UI', sans-serif;
            }
            QListWidget {
                background: transparent;
                border: none;
                color: #1A1A1A;
                font-size: 14px;
                outline: 0;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 6px;
                margin-bottom: 2px;
            }
            QListWidget::item:hover {
                background-color: rgba(0, 0, 0, 15);
                color: #000000;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 4px 2px 4px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 40);
                min-height: 30px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 80);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """
    else:
        return """
            #PocketWindow {
                background-color: rgba(30, 30, 30, 245);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 25);
                font-family: 'Segoe UI', sans-serif;
            }
            QListWidget {
                background: transparent;
                border: none;
                color: #E0E0E0;
                font-size: 14px;
                outline: 0;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 6px;
                margin-bottom: 2px;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 20);
                color: #FFFFFF;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 4px 2px 4px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 60);
                min-height: 30px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 120);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """

def get_settings_style(theme: str) -> str:
    if theme == "light":
        return """
            QWidget { background-color: #F3F3F3; color: #1A1A1A; font-size: 14px; font-family: 'Segoe UI', sans-serif; }
            QPushButton { background-color: #E1E1E1; border: 1px solid #CCC; border-radius: 5px; padding: 8px; color: #1A1A1A; }
            QPushButton:hover { background-color: #D1D1D1; }
            QComboBox { background-color: #FFF; border: 1px solid #CCC; border-radius: 4px; padding: 6px; color: #1A1A1A; }
            QComboBox::drop-down { border: none; }
            QSlider::groove:horizontal { border: 1px solid #CCC; height: 4px; background: #E1E1E1; margin: 2px 0; border-radius: 2px; }
            QSlider::handle:horizontal { background: #0078D7; border: 1px solid #0078D7; width: 14px; margin: -5px 0; border-radius: 7px; }
        """
    else:
        return """
            QWidget { background-color: #1E1E1E; color: white; font-size: 14px; font-family: 'Segoe UI', sans-serif; }
            QPushButton { background-color: #333; border: 1px solid #555; border-radius: 5px; padding: 8px; color: white; }
            QPushButton:hover { background-color: #444; }
            QComboBox { background-color: #333; border: 1px solid #555; border-radius: 4px; padding: 6px; color: white; }
            QComboBox::drop-down { border: none; }
            QSlider::groove:horizontal { border: 1px solid #555; height: 4px; background: #333; margin: 2px 0; border-radius: 2px; }
            QSlider::handle:horizontal { background: #4DA1FF; border: 1px solid #4DA1FF; width: 14px; margin: -5px 0; border-radius: 7px; }
        """