import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QDialog, QMainWindow, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel

from linkedinObjects import LinkedinInstance, LinkedinProfile, LoginStatus


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")

        main_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Login to Linkedin")
        self.login_button.clicked.connect(self.__login__)

        self.status_label = QLabel("")

        main_layout.addRow('Username:', self.username_edit)
        main_layout.addRow('Password:', self.password_edit)
        main_layout.addRow(self.login_button)
        main_layout.addRow(self.status_label)

        self.instance = LinkedinInstance()

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setLayout(main_layout)
        self.show()

    def __set_status_text__(self, text: str):
        self.status_label.setText(text)

    def __login__(self):
        login_status = self.instance.attempt_login(self.username_edit.text(), self.password_edit.text())
        if login_status == LoginStatus.SUCCESS:
            self.__set_status_text__("Login successful")
            self.accept()
        elif login_status == LoginStatus.VERIFY:
            self.__set_status_text__("Login successful. Please complete captcha")
        elif login_status == LoginStatus.FAIL:
            self.__set_status_text__("Login failed")

    def closeEvent(self, a0):
        print("Close")


class ScraperDialog(QDialog):
    def __init__(self, linkedin_instance: LinkedinInstance):
        super().__init__()
        self.setWindowTitle("Scraper")

        if linkedin_instance is None:
            self.reject()
            return

        self.linkedin_instance: LinkedinInstance = linkedin_instance
        self.linkedin_profile: LinkedinProfile = None
        main_layout = QFormLayout()

        self.target_slug_edit = QLineEdit()

        slug_button = QPushButton("Set Slug")
        slug_button.clicked.connect(self.__set_slug__)

        self.scrape_button = QPushButton("Scrape Profile")
        self.scrape_button.clicked.connect(self.__scrape__)
        self.save_button = QPushButton("Generate CV")
        self.save_button.clicked.connect(self.__to_cv__)

        self.status_label = QLabel("")
        self.status_label.setTextFormat(Qt.TextFormat.RichText)

        main_layout.addRow('Slug:', self.target_slug_edit)
        main_layout.addRow(slug_button)
        main_layout.addRow(self.scrape_button)
        main_layout.addRow(self.save_button)
        main_layout.addRow(self.status_label)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setLayout(main_layout)
        self.show()

    def __set_status_text__(self, text: str):
        self.status_label.setText(text)

    def __set_slug__(self):
        self.linkedin_profile = LinkedinProfile(self.target_slug_edit.text())

    def __scrape__(self):
        if self.linkedin_profile is None:
            self.__set_status_text__('<a style="color:red;">Please set a profile slug "https://linkedin.com/in/<u>johndoe</u>"</a>')
            return
        self.linkedin_instance.scrape_profile(self.linkedin_profile)
        self.__set_status_text__(
            '<a style="color:green;">Successfully scraped profile</a>')

    def __to_cv__(self):
        if self.linkedin_profile is None:
            self.__set_status_text__('<a style="color:red;">Please set a profile slug "https://linkedin.com/in/<u>johndoe</u>"</a>')
            return

        # Open a file dialog to ask for a save path
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            caption="Save DOCX File",
            filter="DOCX Files (*.docx)"
        )

        # The save_path will be an empty string if the user cancels the dialog
        if save_path:
            self.linkedin_profile.create_cv().save(save_path)
            self.__set_status_text__('<a style="color:Green;">Successfully generated CV</a>')
        else:
            self.__set_status_text__('<a style="color:red;">Invalid save path</a>')

    def closeEvent(self, a0):
        if self.linkedin_instance is not None:
            self.linkedin_instance.terminate()
        super().closeEvent(a0)


def create_application():
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()

    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        print("Success")
        scraper_dialog = ScraperDialog(login_dialog.instance)
        if scraper_dialog.exec() == QDialog.DialogCode.Accepted:
            print("Success")
        else:
            print("Fail")
    else:
        print("Fail")
