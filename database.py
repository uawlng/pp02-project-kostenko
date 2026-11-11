import psycopg
from psycopg_pool import ConnectionPool

class Database:
    def __init__(self):
        self.connection_pool = None
        try:
            self.connection_pool = ConnectionPool(
                conninfo="host=localhost port=5432 dbname=sad_i_ogorod user=postgres password=123",
                min_size=1,
                max_size=5,
                open=True
            )
            print("Пул соединений создан")
        except psycopg.Error as e:
            print(f"Ошибка БД: {e}")
            self.connection_pool = None

    def get_connection(self):
        if self.connection_pool is not None:
            return self.connection_pool.getconn()
        return None

    def release_connection(self, conn):
        if self.connection_pool is not None and conn is not None:
            self.connection_pool.putconn(conn)

    def close_all(self):
        if self.connection_pool is not None:
            self.connection_pool.close()
            print("Пул закрыт")

    def get_categories(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name FROM categories ORDER BY name")
                categories = cursor.fetchall()
                return [row[0] for row in categories]
        except psycopg.Error as e:
            print(f"Ошибка запроса категорий: {e}")
            return []
        finally:
            self.release_connection(conn)

    def get_products(self, search="", category="Все категории", sort_order="Без сортировки"):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                search_pattern = f"%{search}%"

                order_map = {
                    "Цена: по возрастанию": "p.price ASC",
                    "Цена: по убыванию": "p.price DESC",
                    "Количество: по возрастанию": "total_quantity ASC",
                    "Количество: по убыванию": "total_quantity DESC",
                }
                order_clause = ""
                if sort_order in order_map:
                    order_clause = f"ORDER BY {order_map[sort_order]}"

                query = f"""
                    SELECT p.product_id, p.name, p.price, p.image,
                           COALESCE(m.name, 'Неизвестно') AS manufacturer,
                           COALESCE(SUM(si.quantity), 0) AS total_quantity,
                           COALESCE(c.name, 'Без категории') AS category_name
                    FROM products p
                    LEFT JOIN manufacturers m ON p.manufacturer_id = m.manufacturer_id
                    LEFT JOIN categories c ON p.category_id = c.category_id
                    LEFT JOIN stock_items si ON p.product_id = si.product_id
                    WHERE (p.name ILIKE %s OR COALESCE(m.name, '') ILIKE %s)
                    AND (c.name = %s OR %s = 'Все категории')
                    GROUP BY p.product_id, p.name, p.price, p.image, m.name, c.name
                    {order_clause}
                """

                cursor.execute(query, (search_pattern, search_pattern, category, category))
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка запроса: {e}")
            return []
        finally:
            self.release_connection(conn)

    def create_order_safe(self, user_id, status_name, items):
        conn = self.get_connection()
        if conn is None:
            return None, "Нет соединения с БД"
        try:
            with conn.cursor() as cursor:
                # Ищем ID статуса по его названию из таблицы order_statuses
                cursor.execute("SELECT status_id FROM order_statuses WHERE name = %s", (status_name,))
                status_res = cursor.fetchone()
                if not status_res:
                    raise Exception(f"Статус '{status_name}' не найден в БД")
                status_id = status_res[0]

                # Создаем заказ с найденным status_id
                cursor.execute(
                    "INSERT INTO orders (user_id, status_id, order_date) VALUES (%s, %s, CURRENT_DATE) RETURNING order_id",
                    (user_id, status_id)
                )
                order_id = cursor.fetchone()[0]

                for item in items:
                    product_id = item['product_id']
                    variant_id = item['variant_id']
                    qty = item['quantity']
                    price = item['price']

                    cursor.execute(
                        "SELECT stock_item_id FROM stock_items WHERE product_id = %s AND variant_id = %s",
                        (product_id, variant_id)
                    )
                    stock_res = cursor.fetchone()
                    if not stock_res:
                        raise Exception("Товар с выбранным вариантом не найден на складе.")
                    stock_item_id = stock_res[0]

                    cursor.execute(
                        "UPDATE stock_items SET quantity = quantity - %s WHERE stock_item_id = %s AND quantity >= %s",
                        (qty, stock_item_id, qty)
                    )
                    
                    if cursor.rowcount != 1:
                        raise Exception("Недостаточно товара на складе для выбранного варианта")

                    cursor.execute(
                        "INSERT INTO order_items (order_id, stock_item_id, quantity, price, variant_id) VALUES (%s, %s, %s, %s, %s)",
                        (order_id, stock_item_id, qty, price, str(variant_id))
                    )
            conn.commit()
            return order_id, None
        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            self.release_connection(conn)

    def get_all_orders(self):
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT o.order_id, 
                           COALESCE(u.last_name, '') || ' ' || COALESCE(u.first_name, '') || ' ' || COALESCE(u.middle_name, '') AS fio,
                           COUNT(oi.order_item_id) AS items_count,
                           SUM(oi.quantity * oi.price) AS total_sum,
                           COALESCE(s.name, 'Неизвестно') AS status_name
                    FROM orders o
                    LEFT JOIN users u ON o.user_id = u.user_id
                    LEFT JOIN order_items oi ON o.order_id = oi.order_id
                    LEFT JOIN order_statuses s ON o.status_id = s.status_id
                    GROUP BY o.order_id, u.last_name, u.first_name, u.middle_name, s.name
                    ORDER BY o.order_id DESC
                """
                cursor.execute(query)
                return cursor.fetchall()
        except psycopg.Error as e:
            print(f"Ошибка получения заказов: {e}")
            return []
        finally:
            self.release_connection(conn)