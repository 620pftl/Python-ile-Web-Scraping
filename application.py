from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QWidget,
    QMainWindow,
    QPushButton,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QStackedWidget,
)
from PyQt5 import uic
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
import webbrowser
from datetime import datetime


class FirstPage(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("arama_interface.ui", self)

        self.lineEdit.returnPressed.connect(self.search_product)

    def search_product(self):
        product_name = self.lineEdit.text()
        product_name = product_name.replace(" ", "%20")
        self.lineEdit.clear()

        data_frame = pd.DataFrame(columns=["İsim", "Fiyat", "Link"])

        for page in range(5):
            url = (
                "https://www.hepsiburada.com/ara?q="
                + product_name
                + f"&siralama=artanfiyat&sayfa={page}"
            )
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                prices = []
                products = soup.find_all(
                    "li", attrs={"class": "productListContent-zAP0Y5msy8OHn5z7T_K_"}
                )

                for product in products:
                    isim = product.find(
                        "h3", attrs={"data-test-id": "product-card-name"}
                    ).text
                    fiyat = product.find(
                        "div", attrs={"data-test-id": "price-current-price"}
                    ).text
                    link_class = product.find(
                        "div", attrs={"class": "moria-ProductCard-joawUM"}
                    )
                    link = "www.hepsiburada.com" + link_class.a.get("href")

                    data = {"İsim": isim, "Fiyat": fiyat, "Link": link}
                    data = pd.DataFrame.from_dict([data])
                    data_frame = pd.concat([data_frame, data], ignore_index=True)

            else:
                break

        data_frame = data_frame.convert_dtypes()

        data_frame["AsilFiyat"] = data_frame["Fiyat"].str.replace(" TL", "")
        data_frame["AsilFiyat"] = data_frame["AsilFiyat"].str.split(",").str[0]
        data_frame["AsilFiyat"] = data_frame["AsilFiyat"].str.replace(".", "")

        data_frame["AsilFiyat"] = data_frame["AsilFiyat"].astype("int64")

        data_frame["Marka"] = data_frame["İsim"].str.split(" ").str[0]
        data_frame["Marka"] = data_frame["Marka"].astype("string")

        # Create an SQLite database connection
        engine = create_engine("sqlite:///request.db")

        # Save the DataFrame to the database
        data_frame.to_sql("users", engine, if_exists="replace", index=False)

        window2 = SecondPage()
        widgets.addWidget(window2)
        widgets.setCurrentIndex(widgets.currentIndex() + 1)


class SecondPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(200, 200, 1200, 600)  # set the size of the window

        widgets.setWindowTitle("Ürünler")
        # filter bar
        self.name_edit = QLineEdit()
        self.name_edit.setFixedSize(600, 40)
        self.name_edit.setStyleSheet("font-size: 10pt;")

        # Create a table widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setColumnWidth(0, 400)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 400)
        self.table.setColumnWidth(3, 200)

        self.table.setHorizontalHeaderLabels(["Ürün", "Fiyat", "Link", "Marka"])

        # Connect to the database and retrieve the products
        conn = sqlite3.connect("request.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        products = cursor.fetchall()

        # Populate the table with the products
        self.table.setRowCount(len(products))
        for i, product in enumerate(products):
            product_name, price, link, asilfiyat, marka = product
            self.table.setItem(i, 0, QTableWidgetItem(str(product_name)))
            self.table.setItem(i, 1, QTableWidgetItem(price))
            self.table.setItem(i, 2, QTableWidgetItem(link))
            self.table.setItem(i, 3, QTableWidgetItem(marka))

        # self.table.resizeColumnsToContents()

        # Add the table to the layout
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.name_edit)
        layout.addLayout(filter_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.table.cellClicked.connect(self.open_url)
        self.name_edit.returnPressed.connect(self.filter_content)

    def open_url(self, row, column):
        url = self.table.item(row, 2).text()
        webbrowser.open(url)

    def filter_content(self):
        text = self.name_edit.text()
        conn = sqlite3.connect("request.db")
        # Create a cursor object
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE Marka = '{text}'"
        c.execute(query)
        global filteredProducts
        filteredProducts = c.fetchall()

        window3 = ThirdPage()
        window3.close()
        window3 = ThirdPage()
        widgets.addWidget(window3)
        widgets.setCurrentIndex(widgets.currentIndex() + 1)


class ThirdPage(QMainWindow):
    def __init__(self):
        super().__init__()
        widgets.setWindowTitle("Filtrelenmiş Ürünler")
        # self.setGeometry(200, 200, 1200, 600) # set the size of the window

        self.pushButton = QPushButton()
        self.pushButton.setText("Geri")
        self.pushButton.setStyleSheet("font-size: 12pt;")
        self.pushButton.setGeometry(550, 520, 200, 80)

        # Create a table widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setColumnWidth(0, 400)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 400)
        self.table.setColumnWidth(3, 200)

        self.table.setHorizontalHeaderLabels(["Ürün", "Fiyat", "Link", "Marka"])

        self.table.setRowCount(len(filteredProducts))
        for i, product in enumerate(filteredProducts):
            product_name, price, link, asilfiyat, marka = product
            self.table.setItem(i, 0, QTableWidgetItem(str(product_name)))
            self.table.setItem(i, 1, QTableWidgetItem(price))
            self.table.setItem(i, 2, QTableWidgetItem(link))
            self.table.setItem(i, 3, QTableWidgetItem(marka))

            # Add the table to the layout
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        central_widget = QWidget()

        layout.addWidget(self.pushButton)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.table.cellClicked.connect(self.open_url)
        self.pushButton.clicked.connect(self.go_back)
        widgets.currentChanged.connect(self.update_data)

    def open_url(self, row, column):
        name, price, link, asilFiyat, marka = filteredProducts[row]
        now = datetime.now()
        current_date = now.strftime("%d-%m-%Y")
        current_time = now.strftime("%H:%M")

        my_data = pd.DataFrame(
            columns=["İsim", "Fiyat", "Link", "AsilFiyat", "Marka", "Tarih", "Saat"]
        )
        data_temp = {
            "İsim": name,
            "Fiyat": price,
            "Link": link,
            "AsilFiyat": asilFiyat,
            "Marka": marka,
            "Tarih": current_date,
            "Saat": current_time,
        }
        data_temp = pd.DataFrame.from_dict([data_temp])
        my_data = pd.concat([my_data, data_temp], ignore_index=True)

        # Create an SQLite database connection
        engine = create_engine("sqlite:///begenilenUrunler.db")
        # Save the DataFrame to the database
        my_data.to_sql("begenilenler", engine, if_exists="append", index=False)

        # go to url
        url = self.table.item(row, 2).text()
        webbrowser.open(url)

    def go_back(self):
        widgets.setWindowTitle("Ürünler")
        widgets.setCurrentIndex(widgets.currentIndex() - 1)

    def update_data(self):
        self.table.setRowCount(len(filteredProducts))
        for i, product in enumerate(filteredProducts):
            product_name, price, link, asilfiyat, marka = product
            self.table.setItem(i, 0, QTableWidgetItem(str(product_name)))
            self.table.setItem(i, 1, QTableWidgetItem(price))
            self.table.setItem(i, 2, QTableWidgetItem(link))
            self.table.setItem(i, 3, QTableWidgetItem(marka))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window1 = FirstPage()

    widgets = QStackedWidget()
    widgets.addWidget(window1)
    widgets.setFixedHeight(600)
    widgets.setFixedWidth(1200)
    widgets.setWindowTitle("Arama Sayfası")
    widgets.show()
    sys.exit(app.exec_())
