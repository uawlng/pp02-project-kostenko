import os
import sys
from decimal import Decimal
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QComboBox, QScrollArea, QMessageBox, QStackedWidget,
                               QDialog, QInputDialog, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QAbstractItemView)
from database import Database
from discount import calculate_price 


class OrderDetailsDialog(QDialog):
    def __init__(self, order_id, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.order_id = order_id
        self.setWindowTitle(f"Состав заказа №{order_id}")
        self.resize(650, 450)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        
        self.layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Товар", "Количество", "Цена", "Сумма"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF; color: #000000; gridline-color: #cccccc; font-size: 14px;
            }
            QHeaderView::section {
                background-color: #D2F6E7; color: #2c3e50; padding: 5px; border: 1px solid #cccccc; font-weight: bold;
            }
            QTableWidget::item { padding: 5px; }
        """)
        self.layout.addWidget(self.table)
        
        self.total_label = QLabel("Итого: 0.00 ₽")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        self.total_label.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.total_label)
        
        btn_layout = QHBoxLayout()
        
        self.btn_delete = QPushButton("Удалить выбранную позицию")
        self.btn_delete.setStyleSheet("background-color: #d9534f; color: white; padding: 8px; border-radius: 4px;")
        self.btn_delete.clicked.connect(self.delete_item)
        btn_layout.addWidget(self.btn_delete)
        
        btn_close = QPushButton("Закрыть")
        btn_close.setStyleSheet("background-color: #70B2AF; color: white; padding: 8px; border-radius: 4px;")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        self.layout.addLayout(btn_layout)
        
        self.load_order_details(order_id)
        self.load_total(order_id)
        
    def load_order_details(self, order_id):
        if not order_id:
            return
            
        items = self.db.get_order_details(order_id)
        
        self.table.setRowCount(0)
        if not items:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("В этом заказе нет товаров."))
            self.table.setSpan(0, 0, 1, 4)
            return
            
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            product_name = item[0]
            qty = item[1]
            price = float(item[2])
            total = float(item[3])
            
            self.table.setItem(row, 0, QTableWidgetItem(product_name))
            self.table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{price:.2f} ₽"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{total:.2f} ₽"))

    def load_total(self, order_id):
        if not order_id:
            return
        total = self.db.get_order_total(order_id)
        self.total_label.setText(f"Итого: {float(total):.2f} ₽")

    def delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите позицию для удаления.")
            return
            
        product_name = self.table.item(row, 0).text()
        if product_name == "В этом заказе нет товаров.":
            return
            
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить «{product_name}» из заказа?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_order_item(self.order_id, product_name)
            self.load_order_details(self.order_id)
            self.load_total(self.order_id)


class ProductCard(QDialog):
    def __init__(self, product, main_window):
        super().__init__()
        self.product = product
        self.main_window = main_window
        self.setWindowTitle("Карточка товара")
        self.resize(450, 700)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.update_image_label(self.product[3])
        
        self.name_label = QLabel(f"{self.product[1]}")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        
        info_text = (
            f"<b>Производитель:</b> {self.product[4]}<br>"
            f"<b>Категория:</b> {self.product[6]}<br>"
            f"<b>Состав:</b> {self.product[7] if len(self.product) > 7 else 'Не указан'}<br>"
            f"<b>Описание:</b> {self.product[8] if len(self.product) > 8 else '—'}"
        )
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #333333; font-size: 13px;")
        
        base_price = float(self.product[2]) if self.product[2] else 0.0
        final_price, discount_amount = calculate_price(self.product[0], base_price)
        if final_price is None:
            final_price = base_price
            discount_amount = 0.0

        if discount_amount > 0:
            price_text = f"<span style='color:red;'><s>{base_price:.2f} ₽</s></span> <b>{final_price:.2f} ₽</b>"
        else:
            price_text = f"<b>{final_price:.2f} ₽</b>"
        price_label = QLabel(price_text)
        price_label.setStyleSheet("font-size: 18px; color: #2c3e50;")

        self.variant_combo = QComboBox()
        self.variant_combo.setStyleSheet(
            "padding: 5px; font-size: 14px; border: 1px solid #ccc; "
            "color: #000000; background-color: #FFFFFF;"
        )
        variants = self.main_window.db.get_variants()
        for v_id, v_name in variants:
            avail = self.main_window.db.get_stock_quantity(self.product[0], v_id)
            self.variant_combo.addItem(f"{v_name} (доступно: {avail} шт.)", v_id)
        self.variant_combo.currentIndexChanged.connect(self.update_available_hint)

        self.available_label = QLabel("")
        self.available_label.setStyleSheet("font-size: 13px; color: #555555;")
        self.update_available_hint()

        lbl_variant = QLabel("Выберите вариант:")
        lbl_variant.setStyleSheet("font-weight: bold; color: #000000; font-size: 14px;")

        self.btn_add = QPushButton("Добавить в корзину")
        self.btn_add.setStyleSheet(
            "background-color: #70B2AF; color: white; padding: 10px; "
            "border-radius: 5px; font-weight: bold; font-size: 14px; border: none;"
        )
        self.btn_add.clicked.connect(self.add_to_cart_click)
        
        if self.main_window.role_id == 0:
            self.btn_add.hide()

        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        layout.addWidget(price_label)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addWidget(lbl_variant)
        layout.addWidget(self.variant_combo)
        layout.addWidget(self.available_label)
        layout.addWidget(self.btn_add)

    def update_image_label(self, image_name):
        if not image_name:
            self.image_label.setText("Фото отсутствует")
            self.image_label.setStyleSheet("border: 1px solid #ccc; padding: 40px; color: #888888; font-size: 14px;")
            return
        clean_name = os.path.basename(image_name)
        path = os.path.join("images", clean_name)
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_label.setText("Фото отсутствует")
            self.image_label.setStyleSheet("border: 1px solid #ccc; padding: 40px; color: #888888; font-size: 14px;")
        else:
            self.image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_available_hint(self):
        variant_id = self.variant_combo.currentData()
        if variant_id is None:
            self.available_label.setText("")
            return
        avail = self.main_window.db.get_stock_quantity(self.product[0], variant_id)
        if avail > 0:
            self.available_label.setText(f"Доступно для заказа: {avail} шт.")
        else:
            self.available_label.setText("Нет в наличии для выбранного варианта")

    def add_to_cart_click(self):
        variant_id = self.variant_combo.currentData()
        if variant_id is None:
            QMessageBox.warning(self, "Внимание", "Не выбран вариант исполнения.\nВыберите вариант из списка.")
            return
        available = self.main_window.db.get_stock_quantity(self.product[0], variant_id)
        if available <= 0:
            QMessageBox.warning(self, "Нет в наличии", f"Вариант отсутствует на складе.\nВыберите другой вариант.")
            return
        qty, ok = QInputDialog.getInt(self, "Количество", f"Доступно: {available} шт.\nСколько штук добавить?", 1, 1, available)
        if not ok:
            return
        variant_name = self.variant_combo.currentText().split(" (")[0]
        display_name = f"{self.product[1]} ({variant_name})"
        base_price = float(self.product[2]) if self.product[2] else 0.0
        final_price, _ = calculate_price(self.product[0], base_price)
        if final_price is None:
            final_price = base_price
        self.main_window.add_to_cart(self.product[0], variant_id, display_name, qty, float(final_price))
        self.accept()


def create_card(product, main_window):
    card = QWidget()
    card.setObjectName("productCard")
    total_quantity = product[5] if len(product) > 5 else 0
    base_price = float(product[2]) if product[2] else 0.0
    final_price, discount_amount = calculate_price(product[0], base_price)
    if final_price is None:
        final_price = base_price
        discount_amount = 0.0
    if total_quantity <= 3:
        bg_color, border_color = "#FF8080", "#FF8080"
    else:
        bg_color, border_color = "#FFFFFF", "#000000"
    card.setStyleSheet(f"#productCard {{ border: 1px solid {border_color}; border-radius: 4px; background-color: {bg_color}; }} #productCard QLabel {{ background-color: transparent; font-family: Calibri; }}")
    card.mousePressEvent = lambda event: ProductCard(product, main_window).exec()
    main_layout = QHBoxLayout(card)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(15)
    image_label = QLabel()
    image_label.setFixedSize(100, 100)
    image_label.setAlignment(Qt.AlignCenter)
    image_label.setStyleSheet("border: 1px solid #000000; background-color: #FFFFFF;")
    name = product[1] if product[1] else "Наименование"
    file_name = product[3]
    manufacturer = product[4] if product[4] else "Неизвестный производитель"
    category_name = product[6] if len(product) > 6 else "Без категории"
    material = product[7] if len(product) > 7 and product[7] else "Не указан"
    placeholder_path = os.path.join("resources", "picture.png")
    if file_name:
        clean_name = os.path.basename(file_name)
        image_path = os.path.join("images", clean_name)
    else:
        image_path = placeholder_path
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        pixmap = QPixmap(placeholder_path)
    if pixmap.isNull():
        image_label.setText("IMG")
    else:
        image_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    main_layout.addWidget(image_label)
    text_layout = QVBoxLayout()
    text_layout.setSpacing(3)
    text_style = "font-size: 14px; border: none; color: #000000; font-family: Calibri;"
    title = QLabel(f"{manufacturer} | {name}")
    title.setStyleSheet(text_style + " font-weight: bold;")
    category_label = QLabel(f"Категория: {category_name}")
    category_label.setStyleSheet(text_style)
    quantity_text = f"Количество: {total_quantity} шт." if total_quantity > 0 else "Нет в наличии"
    quantity_label = QLabel(quantity_text)
    if total_quantity == 0:
        quantity_label.setStyleSheet("font-size: 14px; border: none; color: #d9534f; font-weight: bold; font-family: Calibri;")
    else:
        quantity_label.setStyleSheet(text_style)
    material_label = QLabel(f"Состав: {material}")
    material_label.setStyleSheet(text_style)
    text_layout.addWidget(title)
    text_layout.addWidget(category_label)
    text_layout.addWidget(quantity_label)
    text_layout.addWidget(material_label)
    text_layout.addStretch()
    main_layout.addLayout(text_layout, 1)
    price_layout = QVBoxLayout()
    price_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
    if discount_amount > 0:
        old_price_label = QLabel(f"<s>{base_price:.2f} ₽</s>")
        old_price_label.setAlignment(Qt.AlignRight)
        old_price_label.setStyleSheet("color: red; font-size: 14px; border: none; font-family: Calibri;")
        price_layout.addWidget(old_price_label)
    new_price_label = QLabel(f"{final_price:.2f} ₽")
    new_price_label.setAlignment(Qt.AlignRight)
    new_price_label.setStyleSheet("color: black; font-weight: bold; font-size: 16px; border: none; font-family: Calibri;")
    price_layout.addWidget(new_price_label)
    main_layout.addLayout(price_layout)
    return card


class MainWindow(QMainWindow):
    def __init__(self, role_id=None, full_name=None, db=None, user_id=None):
        super().__init__()
        self.role_id = role_id if role_id is not None else 0
        self.full_name = full_name
        self.db = db if db is not None else Database()
        self.user_id = user_id
        self.setWindowTitle("Сад и огород — Каталог")
        self.resize(900, 700)
        self.setWindowIcon(QIcon("resources/icon.ico"))
        font = QFont("Calibri", 10)
        self.setFont(font)
        self.setStyleSheet("""
            QMainWindow { background-color: #FFFFFF; font-family: Calibri; }
            QLabel { font-family: Calibri; }
            #HeaderLabel { font-size: 28px; font-weight: bold; color: #2c3e50; margin: 20px; }
            QPushButton { padding: 10px; margin: 5px; font-size: 14px; background-color: #70B2AF; color: white; border: none; border-radius: 5px; font-family: Calibri; }
            QPushButton:hover { background-color: #5a9a97; }
            QComboBox, QLineEdit { padding: 5px; font-size: 14px; font-family: Calibri; border: 1px solid #ccc; border-radius: 3px; }
        """)
        self.setup_ui()
        self.setup_role_interface()
        self.load_products()

    def setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #D2F6E7; border-radius: 5px;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)
        logo_header = QLabel()
        pixmap_logo = QPixmap("resources/logo.png")
        if not pixmap_logo.isNull():
            logo_header.setPixmap(pixmap_logo.scaledToHeight(50, Qt.SmoothTransformation))
        header_layout.addWidget(logo_header)
        header_layout.addStretch()
        name_text = f"ФИО: {self.full_name}" if self.full_name else "ФИО: —"
        name_label = QLabel(name_text)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; background-color: transparent;")
        header_layout.addWidget(name_label)
        self.logout_button = QPushButton("Выход")
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setFixedSize(80, 30)
        self.logout_button.setStyleSheet("""
            QPushButton { background-color: #70B2AF; color: white; border: none; border-radius: 4px; font-size: 13px; padding: 0px; margin: 0px; }
            QPushButton:hover { background-color: #5a9a97; }
        """)
        header_layout.addWidget(self.logout_button)
        main_layout.addWidget(header_widget)

        nav_layout = QHBoxLayout()
        self.back_button = QPushButton("Назад")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.hide()
        nav_layout.addWidget(self.back_button)
        self.title_label = QLabel("Сад и огород — Каталог")
        self.title_label.setObjectName("HeaderLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(self.title_label, 1)
        main_layout.addLayout(nav_layout)

        self.stacked_widget = QStackedWidget()

        self.page_catalog = QWidget()
        catalog_layout = QVBoxLayout(self.page_catalog)
        controls_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск")
        self.search_input.textChanged.connect(self.load_products)
        controls_layout.addWidget(self.search_input, 2)
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все категории")
        categories = self.db.get_categories()
        for cat in categories:
            self.filter_combo.addItem(cat)
        self.filter_combo.currentIndexChanged.connect(self.load_products)
        controls_layout.addWidget(self.filter_combo, 1)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Без сортировки", "Цена: по возрастанию", "Цена: по убыванию"])
        self.sort_combo.currentIndexChanged.connect(self.load_products)
        controls_layout.addWidget(self.sort_combo, 1)
        catalog_layout.addLayout(controls_layout)
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignLeft)
        self.orders_button = QPushButton("Заказы")
        self.orders_button.clicked.connect(self.open_orders_page)
        btn_layout.addWidget(self.orders_button, 1)
        self.order_button = QPushButton("Перейти в корзину")
        self.order_button.clicked.connect(self.open_cart_page)
        self.order_button.setFixedWidth(160)
        btn_layout.addWidget(self.order_button, 0)
        catalog_layout.addLayout(btn_layout)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: #FFFFFF")
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.container)
        catalog_layout.addWidget(self.scroll)

        self.page_orders = QWidget()
        orders_layout = QVBoxLayout(self.page_orders)
        self.role_stack = QStackedWidget()
        table_style = """
            QTableWidget { background-color: #FFFFFF; color: #000000; gridline-color: #cccccc; font-size: 14px; }
            QHeaderView::section { background-color: #D2F6E7; color: #2c3e50; padding: 5px; border: 1px solid #cccccc; font-weight: bold; }
            QTableWidget::item { padding: 5px; }
        """

        self.page_manager = QWidget()
        mgr_layout = QVBoxLayout(self.page_manager)
        mgr_layout.addWidget(QLabel("<h2>Панель Менеджера</h2>"))
        mgr_btn_layout = QHBoxLayout()
        self.add_order_button = QPushButton("Добавить заказ")
        self.add_order_button.clicked.connect(lambda: QMessageBox.information(self, "Заказ", "Форма добавления заказа"))
        self.add_order_button.setFixedWidth(150)
        mgr_btn_layout.addWidget(self.add_order_button)
        mgr_btn_layout.addStretch()
        mgr_layout.addLayout(mgr_btn_layout)

        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Дата", "ФИО клиента", "Сумма", "Статус"])
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.orders_table.setColumnHidden(0, True)
        
        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.orders_table.setColumnWidth(0, 0)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.orders_table.setStyleSheet(table_style)
        self.orders_table.cellClicked.connect(self.on_order_click)
        mgr_layout.addWidget(self.orders_table, 1)

        self.page_admin = QWidget()
        admin_layout = QVBoxLayout(self.page_admin)
        admin_layout.addWidget(QLabel("<h2>Панель Администратора</h2>"))
        admin_btn_layout = QHBoxLayout()
        self.add_order_button_adm = QPushButton("Добавить заказ")
        self.add_order_button_adm.clicked.connect(lambda: QMessageBox.information(self, "Заказ", "Форма добавления заказа"))
        self.add_order_button_adm.setFixedWidth(150)
        admin_btn_layout.addWidget(self.add_order_button_adm)
        self.edit_order_button = QPushButton("Редактировать заказ")
        self.edit_order_button.clicked.connect(lambda: QMessageBox.information(self, "Заказ", "Форма редактирования заказа"))
        self.edit_order_button.setFixedWidth(170)
        admin_btn_layout.addWidget(self.edit_order_button)
        admin_btn_layout.addStretch()
        admin_layout.addLayout(admin_btn_layout)

        self.orders_table_admin = QTableWidget()
        self.orders_table_admin.setColumnCount(5)
        self.orders_table_admin.setHorizontalHeaderLabels(["ID", "Дата", "ФИО клиента", "Сумма", "Статус"])
        self.orders_table_admin.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.orders_table_admin.setEditTriggers(QTableWidget.NoEditTriggers)
        self.orders_table_admin.setColumnHidden(0, True)
        
        header_admin = self.orders_table_admin.horizontalHeader()
        header_admin.setSectionResizeMode(0, QHeaderView.Fixed)
        self.orders_table_admin.setColumnWidth(0, 0)
        header_admin.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_admin.setSectionResizeMode(2, QHeaderView.Stretch)
        header_admin.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_admin.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.orders_table_admin.setStyleSheet(table_style)
        self.orders_table_admin.cellClicked.connect(self.on_order_click)
        admin_layout.addWidget(self.orders_table_admin, 1)

        self.role_stack.addWidget(self.page_manager)
        self.role_stack.addWidget(self.page_admin)
        orders_layout.addWidget(self.role_stack)

        self.page_cart = QWidget()
        cart_layout = QVBoxLayout(self.page_cart)
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Наименование", "Количество", "Цена", "Сумма", "ID"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.setStyleSheet(table_style)
        cart_layout.addWidget(self.cart_table)
        self.total_label = QLabel("Итого: 0.00 ₽")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        self.total_label.setAlignment(Qt.AlignRight)
        cart_layout.addWidget(self.total_label)
        btn_remove = QPushButton("Удалить выбранный товар")
        btn_remove.clicked.connect(self.remove_from_cart)
        cart_layout.addWidget(btn_remove)
        btn_change_qty = QPushButton("Изменить количество")
        btn_change_qty.clicked.connect(self.change_quantity)
        cart_layout.addWidget(btn_change_qty)
        cart_layout.addSpacing(10)
        btn_checkout = QPushButton("Оформить заказ")
        btn_checkout.clicked.connect(self.confirm_order)
        cart_layout.addWidget(btn_checkout)

        self.stacked_widget.addWidget(self.page_catalog)
        self.stacked_widget.addWidget(self.page_orders)
        self.stacked_widget.addWidget(self.page_cart)
        main_layout.addWidget(self.stacked_widget)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def open_orders_page(self):
        self.switch_page(1)
        self.load_orders()

    def open_cart_page(self):
        self.switch_page(2)
        self.update_total()

    def load_orders(self):
        orders = self.db.get_orders_for_table()
        self.orders_table.setRowCount(0)
        self.orders_table_admin.setRowCount(0)
        if not orders:
            return
        for row, order in enumerate(orders):
            order_id = str(order[0])
            date_str = str(order[1])
            fio = str(order[2])
            total_sum = f"{float(order[3]):.2f} ₽"
            status = str(order[4])
            
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(order_id))
            self.orders_table.setItem(row, 1, QTableWidgetItem(date_str))
            self.orders_table.setItem(row, 2, QTableWidgetItem(fio))
            self.orders_table.setItem(row, 3, QTableWidgetItem(total_sum))
            self.orders_table.setItem(row, 4, QTableWidgetItem(status))

            self.orders_table_admin.insertRow(row)
            self.orders_table_admin.setItem(row, 0, QTableWidgetItem(order_id))
            self.orders_table_admin.setItem(row, 1, QTableWidgetItem(date_str))
            self.orders_table_admin.setItem(row, 2, QTableWidgetItem(fio))
            self.orders_table_admin.setItem(row, 3, QTableWidgetItem(total_sum))
            self.orders_table_admin.setItem(row, 4, QTableWidgetItem(status))

    def on_order_click(self, row, column):
        order_id_item = self.sender().item(row, 0)
        if not order_id_item:
            return
        order_id = int(order_id_item.text())
        dialog = OrderDetailsDialog(order_id, self.db, self)
        dialog.exec()

    def add_to_cart(self, product_id, variant_id, name, quantity, price):
        for row in range(self.cart_table.rowCount()):
            id_item = self.cart_table.item(row, 4)
            if (int(id_item.text()) == product_id and id_item.data(Qt.UserRole) == variant_id):
                current_qty = int(self.cart_table.item(row, 1).text())
                new_qty = current_qty + quantity
                avail = self.db.get_stock_quantity(product_id, variant_id)
                if new_qty > avail:
                    QMessageBox.warning(self, "Превышение остатка", f"В корзине уже {current_qty} шт.\nДоступно на складе: {avail} шт.\nМожно добавить не более {avail - current_qty} шт.")
                    return
                self.cart_table.setItem(row, 1, QTableWidgetItem(str(new_qty)))
                self.cart_table.setItem(row, 3, QTableWidgetItem(f"{new_qty * price:.2f}"))
                self.update_total()
                QMessageBox.information(self, "Корзина", f"Количество «{name}» увеличено до {new_qty} шт.")
                return
        row = self.cart_table.rowCount()
        self.cart_table.insertRow(row)
        total = quantity * price
        self.cart_table.setItem(row, 0, QTableWidgetItem(name))
        self.cart_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
        self.cart_table.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
        self.cart_table.setItem(row, 3, QTableWidgetItem(f"{total:.2f}"))
        id_item = QTableWidgetItem(str(product_id))
        id_item.setData(Qt.UserRole, variant_id)
        self.cart_table.setItem(row, 4, id_item)
        self.update_total()
        QMessageBox.information(self, "Корзина", f"«{name}» добавлен в корзину ({quantity} шт.).")

    def change_quantity(self):
        row = self.cart_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Не выбрана позиция для изменения.\nВыделите строку в таблице.")
            return
        try:
            id_item = self.cart_table.item(row, 4)
            product_id = int(id_item.text())
            variant_id = id_item.data(Qt.UserRole)
            avail = self.db.get_stock_quantity(product_id, variant_id)
            new_qty, ok = QInputDialog.getInt(self, "Количество", f"Доступно на складе: {avail} шт.\nВведите новое количество:", int(self.cart_table.item(row, 1).text()), 1, max(avail, 1))
            if ok:
                price = float(self.cart_table.item(row, 2).text())
                self.cart_table.setItem(row, 1, QTableWidgetItem(str(new_qty)))
                self.cart_table.setItem(row, 3, QTableWidgetItem(f"{new_qty * price:.2f}"))
                self.update_total()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить количество.\nПричина: {e}")

    def remove_from_cart(self):
        row = self.cart_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Не выбрана позиция для удаления.\nВыделите строку в таблице.")
            return
        reply = QMessageBox.question(self, "Подтверждение удаления", f"Удалить позицию «{self.cart_table.item(row, 0).text()}» из корзины?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.cart_table.removeRow(row)
            self.update_total()
            QMessageBox.information(self, "Корзина", "Товар удалён из корзины.")

    def update_total(self):
        total = Decimal('0.00')
        for row in range(self.cart_table.rowCount()):
            item = self.cart_table.item(row, 3)
            if item and item.text():
                try:
                    total += Decimal(item.text())
                except Exception:
                    pass
        self.total_label.setText(f"Итого: {total:.2f} ₽")

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.update_title_and_back_button(index)

    def go_back(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.switch_page(current_index - 1)

    def update_title_and_back_button(self, index):
        titles = ["Сад и огород — Каталог", "Сад и огород — Заказы", "Сад и огород — Корзина"]
        if 0 <= index < len(titles):
            self.title_label.setText(titles[index])
            self.setWindowTitle(titles[index])
        if index == 0:
            self.back_button.hide()
        else:
            self.back_button.show()

    def load_products(self):
        for i in reversed(range(self.list_layout.count())):
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        search = self.search_input.text()
        category = self.filter_combo.currentText()
        sort = self.sort_combo.currentText()
        self.products = self.db.get_products(search, category, sort)
        
        if not self.products:
            not_found_label = QLabel("Товары не найдены.")
            not_found_label.setStyleSheet("font-size: 18px; color: #555555; font-weight: bold; margin-top: 20px;")
            not_found_label.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(not_found_label)
        else:
            for product in self.products:
                self.list_layout.addWidget(create_card(product, self))

    def setup_role_interface(self):
        self.orders_button.hide()
        self.order_button.hide()
        self.add_order_button.hide()
        self.add_order_button_adm.hide()
        self.edit_order_button.hide()
        
        if self.role_id == 1:
            self.orders_button.show()
            self.add_order_button_adm.show()
            self.edit_order_button.show()
            self.role_stack.setCurrentIndex(1)
            self.title_label.setText("Сад и огород — Администратор")
        elif self.role_id == 2:
            self.orders_button.show()
            self.add_order_button.show()
            self.role_stack.setCurrentIndex(0)
            self.title_label.setText("Сад и огород — Менеджер")
        elif self.role_id == 3:
            self.order_button.show()
            self.title_label.setText("Сад и огород — Клиент")
        else:
            self.title_label.setText("Сад и огород — Режим гостя")
            QMessageBox.information(self, "Режим гостя",
                "Вы вошли как гость.\nОформление заказов и панель управления недоступны.\n"
                "Для оформления заказа авторизуйтесь как клиент.")
            
    def confirm_order(self):
        if self.cart_table.rowCount() == 0:
            QMessageBox.warning(self, "Пустой заказ", "Ваша корзина пуста.\nДобавьте товары перед оформлением заказа.")
            return

        items_to_save = []
        for row in range(self.cart_table.rowCount()):
            item_id = self.cart_table.item(row, 4)
            if not item_id:
                continue
            product_id = int(item_id.text())
            variant_id = item_id.data(Qt.UserRole)
            quantity = int(self.cart_table.item(row, 1).text())
            price = float(self.cart_table.item(row, 2).text())
            avail = self.db.get_stock_quantity(product_id, variant_id)
            if quantity > avail:
                QMessageBox.warning(self, "Недостаточно товара", f"Позиция «{self.cart_table.item(row, 0).text()}»: в корзине {quantity} шт., доступно {avail} шт.\nУменьшите количество или удалите позицию.")
                return
            items_to_save.append({'product_id': product_id, 'variant_id': variant_id, 'quantity': quantity, 'price': price})

        reply = QMessageBox.question(self, "Подтверждение заказа", f"Подтвердить оформление заказа на {self.total_label.text()}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        order_id, error_msg = self.db.create_order_safe(self.user_id, "Новый", items_to_save)
        
        if order_id:
            QMessageBox.information(self, "Заказ оформлен", f"Заказ №{order_id} успешно оформлен.\nСтатус: Новый.\nДата: {self.db.get_order_date(order_id)}")
            self.cart_table.setRowCount(0)
            self.update_total()
            self.load_products()
            self.switch_page(0)
        else:
            QMessageBox.critical(self, "Ошибка оформления заказа", f"Заказ не сохранён.\n\nПричина: {error_msg}\n\nПроверьте остатки на складе и повторите попытку.\nКорзина сохранена — данные не потеряны.")

    def logout(self):
        reply = QMessageBox.question(self, "Выход", "Вы уверены, что хотите выйти?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            from window_login import LoginWindow
            self.login_window = LoginWindow(self.db)
            self.login_window.show()
            self.close()

    def closeEvent(self, event):
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    from window_login import LoginWindow
    login_window = LoginWindow(db)
    login_window.show()
    exit_code = app.exec()
    db.close_all()
    sys.exit(exit_code)
       