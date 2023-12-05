import MySQLdb
import sshtunnel
import os

import contextlib

@contextlib.contextmanager
def connect_with_tunnel():
    sshtunnel.SSH_TIMEOUT = 5.0
    sshtunnel.TUNNEL_TIMEOUT = 5.0
    with sshtunnel.SSHTunnelForwarder(
        ('ssh.eu.pythonanywhere.com'),
        ssh_username='ctrebbau',
        ssh_password=os.environ['SSH_PYANY_PWD'],
        remote_bind_address=('ctrebbau.mysql.eu.pythonanywhere-services.com', 3306)
    ) as tunnel:
        connection = MySQLdb.connect(
            user='ctrebbau',
            passwd=os.environ['MYSQL_PYANY_DB_PWD'],
            host='127.0.0.1', port=tunnel.local_bind_port,
            db='ctrebbau$autopulse'
        )
        try:
            yield connection
        finally:
            connection.close()

def create_autopulse_db():
    with connect_with_tunnel() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS `ctrebbau$autopulse`;")
        conn.commit()

def create_managers_table():
    with connect_with_tunnel() as conn:
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS Managers(
            id INT PRIMARY KEY,
            name VARCHAR(50)
        );"""
        cursor.execute(query)
        conn.commit()

def create_company_table():
    with connect_with_tunnel() as conn:
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS Companies (
            id INT PRIMARY KEY,
            name VARCHAR(60)
        );"""
        cursor.execute(query)
        conn.commit()

def create_center_table():
    with connect_with_tunnel() as conn:
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS Centers (
            id INT PRIMARY KEY,
            name VARCHAR(70)
        );"""
        cursor.execute(query)
        conn.commit()

def create_vehicle_table():
    with connect_with_tunnel() as conn:
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS Vehicles (
          kendra_id INT NOT NULL,
          plate VARCHAR(10) NOT NULL,
          status VARCHAR(17) NOT NULL,
          date DATE NOT NULL,
          company_id INT NOT NULL,
          center_id INT NOT NULL,
          manager_id INT NOT NULL,
          PRIMARY KEY (date, plate),
          FOREIGN KEY (company_id) REFERENCES Companies(id),
          FOREIGN KEY (center_id) REFERENCES Centers(id),
          FOREIGN KEY (manager_id) REFERENCES Managers(id)
        );"""
        cursor.execute(query)
        conn.commit()

if __name__ == "__main__":
    create_autopulse_db()
    create_managers_table()
    create_company_table()
    create_center_table()
    create_vehicle_table()