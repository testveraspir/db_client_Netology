import psycopg2
import settings


class PostgresSQL:
    def __init__(self, database, user, password):
        self.database = database
        self.user = user
        self.password = password
        try:
            self.connection = psycopg2.connect(database=self.database, user=self.user, password=self.password)
        except psycopg2.OperationalError as error:
            print(f"Ошибка при подключении. {error}")

    def __del__(self):
        try:
            self.connection.close()
            print("Соединение отключено.")
        except Exception as del_ex:
            print(del_ex)

    def __check_first_name(self, first_name):
        if isinstance(first_name, str) and 1 < len(first_name) <= 50:
            return True
        return False

    def __check_last_name(self, last_name):
        if isinstance(last_name, str) and 1 < len(last_name) <= 50:
            return True
        return False

    def __check_email(self, email):
        if type(email) == str and "@" in email and "." in email and email.index(".") > email.index("@") + 1 \
                and email.count("@") == 1 and email.count(".") == 1 and 3 < len(email) <= 20:
            return True
        return False

    def __check_phone_number(self, phone_number):
        if type(phone_number) == str and 6 < len(phone_number) <= 20:
            return True
        return False

    def __check_phone_number_id(self, email, phone_number_id):
        client_id = self.__get_client_id(email)
        with self.connection.cursor() as cursor:
            cursor.execute("""SELECT pn.phone_number_id
                              FROM client AS c
                              LEFT JOIN phone_number AS pn ON c.client_id=pn.client_id
                              WHERE c.client_id=%s;""", (client_id,))
            info_phone_number_id = cursor.fetchall()
            lst_id = []
            for info in info_phone_number_id:
                lst_id.append(info[0])
        if phone_number_id in lst_id:
            return True
        return False

    def __execute_query_with_commit(self, query, values=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, values)
            self.connection.commit()

    def __get_client_id(self, email):
        if not self.__check_email(email):
            return "Некорректный email"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""SELECT client_id FROM client WHERE email=%s;""", (email,))
                client_id = cursor.fetchone()[0]
                return client_id
        except Exception as ex_get_id:
            print(f"Проверить email! {ex_get_id}")

    def create_db(self):
        """Функция, создающая структуру БД(таблицы)."""
        query_1 = """CREATE TABLE IF NOT EXISTS client(
                         client_id SERIAL PRIMARY KEY,
                         first_name VARCHAR(50) NOT NULL,
                         last_name VARCHAR(50) NOT NULL,
                         email VARCHAR(20) NOT NULL UNIQUE);"""
        query_2 = """CREATE TABLE IF NOT EXISTS phone_number(
                         phone_number_id SERIAL PRIMARY KEY,
                         phone_number VARCHAR(20) NOT NULL UNIQUE,
                         client_id INTEGER NOT NULL REFERENCES client(client_id) ON DELETE CASCADE);"""
        try:
            self.__execute_query_with_commit(query_1)
            self.__execute_query_with_commit(query_2)
        except Exception as e:
            print(f"Ошибка при создании таблиц. {e}")

    def del_db(self):
        """Функция, удаляющая все таблицы из базы данных."""
        query_1 = "DROP TABLE IF EXISTS phone_number;"
        query_2 = "DROP TABLE IF EXISTS client;"
        try:
            self.__execute_query_with_commit(query_1)
            self.__execute_query_with_commit(query_2)
        except Exception as ex_del:
            print(f"Ошибка при удалении таблиц из базы данных. {ex_del}")

    def add_client(self, first_name, last_name, email):
        """Функция, позволяющая добавить нового клиента"""
        if not self.__check_first_name(first_name):
            print("Введите корректно имя.")
        elif not self.__check_last_name(last_name):
            print("Введите корректно фамилию.")
        elif not self.__check_email(email):
            print("Введите корректный email.")
        else:
            query = """INSERT INTO client(first_name, last_name, email) VALUES(%s, %s, %s);"""
            values = (first_name, last_name, email)
            try:
                self.__execute_query_with_commit(query, values)
            except Exception as ex_add:
                print(f"{ex_add}")

    def add_phone_number(self, email, phone_number):
        """Функция, позволяющая добавить телефон для существующего клиента по email."""
        client_id = self.__get_client_id(email)
        if self.__check_phone_number(phone_number):
            try:
                query = "INSERT INTO phone_number(phone_number, client_id) VALUES(%s, %s);"
                values = (phone_number, client_id)
                self.__execute_query_with_commit(query, values)
            except Exception as ex_ph:
                print(f"Ошибка при добавлении номера телефона в таблицу phone_number. {ex_ph}")
        else:
            print("Некорректный номер телефона.")

    def change_info_about_client(self, email_current, first_name=None, last_name=None, email=None):
        """Функция, позволяющая изменить данные о клиенте."""
        client_id = self.__get_client_id(email_current)
        count = 0
        try:
            if first_name is not None and self.__check_first_name(first_name):
                query_1 = "UPDATE client SET first_name=%s WHERE client_id=%s;"
                values_1 = (first_name, client_id)
                self.__execute_query_with_commit(query_1, values_1)
                count += 1
            if last_name is not None and self.__check_last_name(last_name):
                query_2 = "UPDATE client SET last_name=%s WHERE client_id=%s;"
                values_2 = (last_name, client_id)
                self.__execute_query_with_commit(query_2, values_2)
                count += 1
            if email is not None and self.__check_last_name(email):
                query_3 = "UPDATE client SET email=%s WHERE client_id=%s;"
                values_3 = (email, client_id)
                self.__execute_query_with_commit(query_3, values_3)
                count += 1
        except Exception as ex_update:
            print(f"Ошибка при изменении данных. {ex_update}")
        if count == 0:
            print("Введите корректные данные.")

    def get_info_phone_number_client(self, email):
        """Функция, позволяющая получить данные о номерах телефона клиентов."""
        try:
            client_id = self.__get_client_id(email)
            with self.connection.cursor() as cursor:
                cursor.execute("""SELECT pn.phone_number_id, pn.phone_number 
                                  FROM client AS c 
                                  LEFT JOIN phone_number AS pn ON c.client_id=pn.client_id 
                                  WHERE c.client_id=%s;""", (client_id,))
                print("phone_number_id, phone_number")
                info_phones = cursor.fetchall()
                if info_phones == [(None, None)]:
                    print(f"У клиента по email {email} нет номеров телефонов.")
                else:
                    for info in info_phones:
                        id_num, name = info
                        print(str(id_num).center(15), name.center(12))
        except Exception as e:
            print(f"Ошибка при получении информации о телефонных номерах клиента. {e}")

    def del_phone_number(self, email, phone_number_id):
        """Функция, позволяющая удалить телефон для существующего клиента."""
        if self.__check_phone_number_id(email, phone_number_id):
            try:
                query = "DELETE FROM phone_number WHERE phone_number_id=%s;"
                values = (phone_number_id,)
                self.__execute_query_with_commit(query, values)
            except Exception as ex_del_num:
                print(f"Ошибка при удалении номера телефона. {ex_del_num}")
        else:
            print(f"По email: {email} не существует телефонного номера с id: {phone_number_id}.")

    def del_client(self, email):
        """Функция, позволяющая удалить существующего клиента."""
        client_id = self.__get_client_id(email)
        query = "DELETE FROM client WHERE client_id=%s;"
        values = (client_id,)
        try:
            self.__execute_query_with_commit(query, values)
        except Exception as ex_del_client:
            print(f"Ошибка при удалении клиента. {ex_del_client}")

    def __query_for_find(self, parameter, value):
        query = f"""SELECT c.first_name, c.last_name, c.email, pn.phone_number
                    FROM client AS c
                    LEFT JOIN phone_number AS pn ON c.client_id=pn.client_id
                    WHERE {parameter}=%s;"""
        values = (value,)
        with self.connection.cursor() as cursor:
            cursor.execute(query, values)
            info = cursor.fetchall()
            print(f"Имя                 Фамилия                email                     телефон")
            for el in info:
                first_name, last_name, email, tel = el
                print(first_name.ljust(19), last_name.ljust(22), email.ljust(25), tel)

    def find_client(self, first_name=None, last_name=None, email=None, phone_number=None):
        """Функция, позволяющая найти клиента по его данным: имени, фамилии, email или телефону."""
        if first_name is not None and self.__check_first_name(first_name):
            self.__query_for_find("c.first_name", first_name)
        elif last_name is not None and self.__check_last_name(last_name):
            self.__query_for_find("c.last_name", last_name)
        elif email is not None and self.__check_email(email):
            self.__query_for_find("c.email", email)
        elif phone_number is not None and self.__check_phone_number(phone_number):
            self.__query_for_find("pn.phone_number", phone_number)
        else:
            print("Введите корректные данные!")


if __name__ == '__main__':
    try:
        conn = PostgresSQL(database=settings.DATABASE, user=settings.USER, password=settings.PASSWORD)
        conn.del_db()
        conn.create_db()

        conn.add_client("Valera", "Petrov", "val@yandex.ru")
        conn.add_client(first_name="Маша", last_name="Иванова", email="m@rambler.ru")
        conn.add_client(first_name="Маша", last_name="Иванова", email="m_ivanova@rambler.ru")
        conn.add_client("Ivan", "Ivanov", "ivan@email.ru")

        conn.add_phone_number("m@rambler.ru", "999-89-11")
        conn.add_phone_number("m@rambler.ru", "999-89-12")
        conn.add_phone_number("ivan@email.ru", "+7911(896)455-11-11")

        conn.change_info_about_client("m@rambler.ru", first_name="Мария")
        conn.change_info_about_client("m@rambler.ru", last_name="Ivanova")
        conn.change_info_about_client("m@rambler.ru", "Маша", "Иванова", "mash@email.ru")
        # Для удаления телефона нужно узнать по email клиента все id телефонов, которые есть у клиента.
        # И выбрать id номера телефона, который нужно удалить.
        conn.get_info_phone_number_client("mash@email.ru")
        # phone_number_id, phone_number
        #       1          999-89-11
        #       3          999-89-12
        conn.del_phone_number("mash@email.ru", 1)
        conn.del_client("ivan@email.ru")

        conn.find_client(first_name="Маша")
        conn.find_client(phone_number="999-89-12")

    except Exception as ex:
        print(f"Введите корректные данные: {ex}")
