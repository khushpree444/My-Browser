from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QToolBar, QAction, QLineEdit, QDialog, QListWidget, 
                             QPushButton, QFormLayout, QRadioButton, QMenu, QMenuBar, QLabel)
from PyQt5.QtWebEngineWidgets import QWebEngineView
import sys
import re

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.history = []  # Initialize history as list of tuples (display_name, url)
        self.bookmarks = []  # Initialize bookmarks as list of tuples (display_name, url)
        self.default_search_engine = "https://www.google.com/search?q="  # Default search engine
        self.home_page = "http://www.google.com"  # Default home page
        self.youtube_url = "https://www.youtube.com"  # YouTube URL
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)  # Enable close button on tabs
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)

        self.urlbar = QLineEdit()  # URL bar
        self.urlbar.returnPressed.connect(self.navigate_to_url)

        self.urlbar.setStyleSheet("""
            QLineEdit {
                border: 2px solid #888;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
            }
        """)

        navtb = QToolBar("Navigation")
        self.addToolBar(navtb)

        navtb.setStyleSheet("""
            QToolBar {
                background: #f0f0f0;
                font-size: 16px;
                height: 40px;
            }
            QToolBar QToolButton {
                padding: 5px;
                border: 1px solid transparent;
            }
            QToolBar QToolButton:hover {
                background: #e0e0e0;
                border: 1px solid #888;
            }
            QToolBar QToolButton:pressed {
                background: #d0d0d0;
            }
        """)

        new_tab_btn = QAction("New Tab", self)
        new_tab_btn.setStatusTip("Open a new tab")
        new_tab_btn.triggered.connect(self.create_new_tab)
        navtb.addAction(new_tab_btn)

        back_btn = QAction("Back", self)
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navtb.addAction(back_btn)

        next_btn = QAction("Forward", self)
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.current_browser().forward())
        navtb.addAction(next_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        navtb.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.setStatusTip("Go home")
        home_btn.triggered.connect(lambda: self.current_browser().setUrl(QUrl(self.home_page)))
        navtb.addAction(home_btn)

        youtube_btn = QAction("YouTube", self)
        youtube_btn.setStatusTip("Open YouTube")
        youtube_btn.triggered.connect(lambda: self.current_browser().setUrl(QUrl(self.youtube_url)))
        navtb.addAction(youtube_btn)

        history_btn = QAction("History", self)
        history_btn.setStatusTip("Show history")
        history_btn.triggered.connect(self.show_history)
        navtb.addAction(history_btn)

        settings_btn = QAction("Settings", self)
        settings_btn.setStatusTip("Open settings")
        settings_btn.triggered.connect(self.open_settings)
        navtb.addAction(settings_btn)

        bookmarks_btn = QAction("Bookmarks", self)
        bookmarks_btn.setStatusTip("Show bookmarks")
        bookmarks_btn.triggered.connect(self.show_bookmarks)
        navtb.addAction(bookmarks_btn)

        navtb.addSeparator()
        navtb.addWidget(self.urlbar)

        stop_btn = QAction("Stop", self)
        stop_btn.setStatusTip("Stop loading current page")
        stop_btn.triggered.connect(lambda: self.current_browser().stop())
        navtb.addAction(stop_btn)

        self.create_new_tab()
        self.show()

    def extract_name_from_url(self, url):
        """Extracts a short, human-readable name from a URL."""
        parsed_url = QUrl(url)
        host = parsed_url.host()
        name = re.sub(r'^www\.', '', host)
        name = re.sub(r'\..*$', '', name)
        return name.capitalize()

    def create_new_tab(self):
        new_tab = QWidget()
        layout = QVBoxLayout()
        browser = QWebEngineView()
        browser.setUrl(QUrl(self.home_page))
        layout.addWidget(browser)
        new_tab.setLayout(layout)

        self.tabs.addTab(new_tab, self.extract_name_from_url(self.home_page))
        self.tabs.setCurrentWidget(new_tab)

        self.urlbar.clear()

        browser.urlChanged.connect(lambda q: self.update_urlbar(browser, q))
        browser.loadFinished.connect(lambda _: self.update_title(browser))
        browser.loadFinished.connect(self.add_to_history)

        # Set up context menu for bookmarks
        browser.setContextMenuPolicy(Qt.CustomContextMenu)
        browser.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        add_bookmark_action = QAction("Add to Bookmark", self)
        add_bookmark_action.triggered.connect(self.add_bookmark)
        context_menu.addAction(add_bookmark_action)
        context_menu.exec_(self.current_browser().mapToGlobal(pos))

    def add_bookmark(self):
        current_url = self.current_browser().url().toString()
        if current_url and not any(url == current_url for _, url in self.bookmarks):
            name = self.extract_name_from_url(current_url)
            self.bookmarks.append((name, current_url))
            self.show_bookmarks()  # Refresh the bookmark dialog

    def show_bookmarks(self):
        bookmarks_dialog = QDialog(self)
        bookmarks_dialog.setWindowTitle("Bookmarks")
        layout = QVBoxLayout()

        bookmarks_list = QListWidget()
        for name, _ in self.bookmarks:
            bookmarks_list.addItem(name)
        bookmarks_list.itemDoubleClicked.connect(self.navigate_from_bookmark)
        layout.addWidget(bookmarks_list)

        clear_btn = QPushButton("Clear Bookmarks")
        clear_btn.clicked.connect(self.clear_bookmarks)
        layout.addWidget(clear_btn)

        bookmarks_dialog.setLayout(layout)
        bookmarks_dialog.exec_()

    def navigate_from_bookmark(self, item):
        for name, url in self.bookmarks:
            if name == item.text():
                self.current_browser().setUrl(QUrl(url))
                break

    def clear_bookmarks(self):
        self.bookmarks.clear()
        self.show_bookmarks()

    def current_browser(self):
        current_tab = self.tabs.currentWidget()
        return current_tab.findChild(QWebEngineView) if current_tab else None

    def update_title(self, browser):
        url = browser.url()
        host = url.host() or "New Tab"
        title = browser.page().title()
        tab_title = host if not title else title

        self.setWindowTitle(f"{tab_title} - My Cool Browser")
        tab_index = self.tabs.indexOf(self.tabs.currentWidget())
        self.tabs.setTabText(tab_index, self.extract_name_from_url(url.toString()))

    def navigate_to_url(self):
        search_text = self.urlbar.text().strip()
        if search_text:
            url = QUrl(search_text)
            if not url.isValid() or url.scheme() == "":
                search_text = f"{self.default_search_engine}{search_text}"
            self.current_browser().setUrl(QUrl(search_text))

    def update_urlbar(self, browser, q):
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def add_to_history(self):
        current_url = self.current_browser().url().toString()
        if current_url and not any(url == current_url for _, url in self.history):
            name = self.extract_name_from_url(current_url)
            self.history.append((name, current_url))

    def show_history(self):
        history_dialog = QDialog(self)
        history_dialog.setWindowTitle("History")
        layout = QVBoxLayout()

        history_list = QListWidget()
        for name, _ in self.history:
            history_list.addItem(name)
        history_list.itemDoubleClicked.connect(self.navigate_from_history)
        layout.addWidget(history_list)

        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)

        history_dialog.setLayout(layout)
        history_dialog.exec_()

    def navigate_from_history(self, item):
        for name, url in self.history:
            if name == item.text():
                self.current_browser().setUrl(QUrl(url))
                break

    def clear_history(self):
        self.history.clear()
        self.show_history()

    def close_current_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.close()  # Close the application if the last tab is closed

    def closeEvent(self, event):
        self.history.clear()  # Clear history on close
        event.accept()  # Continue with the closing process

    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Settings")
        layout = QFormLayout()

        # Create radio buttons for search engine selection
        self.search_engine_radio_buttons = {
            "Google": QRadioButton("Google"),
            "Bing": QRadioButton ("Bing"),
            "Brave": QRadioButton("Brave"),
            "DuckDuckGo": QRadioButton("DuckDuckGo"),
            "Wikipedia": QRadioButton("Wikipedia"),
            # Add more search engines as needed
        }

        for engine, radio in self.search_engine_radio_buttons.items():
            layout.addWidget(radio)
            if self.default_search_engine.startswith(engine.lower()):
                radio.setChecked(True)

        # Save button to apply changes
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        settings_dialog.setLayout(layout)
        settings_dialog.exec_()

    def save_settings(self):
        for engine, radio in self.search_engine_radio_buttons.items():
            if radio.isChecked():
                if engine == "Google":
                    self.default_search_engine = "https://www.google.com/search?q="
                elif engine == "Bing":
                    self.default_search_engine = "https://www.bing.com/search?q="
                elif engine == "Brave":
                    self.default_search_engine = "https://search.brave.com/search?q="
                elif engine == "DuckDuckGo":
                    self.default_search_engine = "https://duckduckgo.com/?q="
                elif engine == "Wikipedia":
                    self.default_search_engine = "https://wikipedia.org/wiki/"

                # Add more search engines as needed

                # Update for more engines if added
                break

        self.show()

        self.save_settings_to_file()

    def save_settings_to_file(self):
        with open("settings.txt", "w") as f:
            f.write(self.default_search_engine)

        print("Settings saved successfully!")

        self.show()
        
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()

