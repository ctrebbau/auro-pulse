import os
import pymysql
import logging
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import time

kndauth = {
    "DB_HOST" : os.environ['KND_HOST'],
    "DB_USER" : os.environ['KND_USER'],
    "DB_PASSWORD" : os.environ['KND_PASSWORD'],
    "DB_NAME" : os.environ['KND_NAME']
    }

localauth = {
    "DB_HOST" : "localhost",
    "DB_USER" : "ctl", 
    "DB_PASSWORD" : "Iamctl",
    "DB_NAME" : "autopulse"
    }

auroids = [5, 53, 56, 57, 59, 64, 123, 131, 132, 229, 234, 248, 62, 535]

cibeleids = [
    67, 122, 124, 125, 126, 127, 128, 129, 196, 197, 232, 238, 239, 246
]
gestionadoids = [
    74, 77, 231, 240, 287, 294, 295, 299, 304, 305, 306, 309, 613, 614, 
    602, 555, 549, 536, 527
]
allids = auroids + cibeleids + gestionadoids

companies = {
    "auro" : auroids,
    "cibeles" : cibeleids,
    "gestionados" : gestionadoids,
    "all" : allids
}


def connect(auth):
    con = None
    while True:
        try:
            con = pymysql.connect(host=auth['DB_HOST'],
                                  user=auth['DB_USER'],
                                  password=auth['DB_PASSWORD'],
                                  db=auth['DB_NAME'])
            break
        except Exception as e:
            logging.warning(f"Failed to connect to {auth['DB_HOST']}: {e}")
            time.sleep(1)
    return con


def get_vehicle_stati():
    con = connect(kndauth)

    auroids = [5, 53, 56, 57, 59, 64, 123, 131, 132, 229, 234, 248, 62, 535]
    cibeleids = [67, 122, 124, 125, 126, 127, 128, 129, 196, 197, 232, 238, 239, 246]
    gestionadoids = [74, 77, 231, 240, 287, 294, 295, 299, 304, 305, 306, 309, 613, 614, 602, 555, 549, 536, 527]

    all_ids = auroids + cibeleids + gestionadoids
    allcompanies = ', '.join(map(str, all_ids))

    query = f"""
        SELECT
            vehicle.id AS kendra_id,
            vehicle.license_plate_number AS plate,
            vehicle.status AS status,
            employee.id as manager_id,
            CONCAT(employee.first_name, ' ', employee.last_name) AS manager,
            vehicle.company_id AS company_id,
            company.name AS company,
            center.id AS center_id,
            center.name AS center
        FROM vehicle
            INNER JOIN company ON vehicle.company_id = company.id
            INNER JOIN center ON vehicle.operating_center_id = center.id
            INNER JOIN vehicle_group ON vehicle.vehicle_group_id = vehicle_group.id
            INNER JOIN employee ON vehicle_group.fleet_manager_id = employee.id 
        WHERE vehicle.company_id IN({allcompanies})
    """
    # print(query)
    with con.cursor() as cursor:
        cursor.execute(query)
        df = pd.DataFrame(cursor.fetchall(), columns=[i[0] for i in cursor.description])
    return df

def insert_vehicle_data(df):
    con = connect(localauth)
    cursor = con.cursor()

    df['date'] = (datetime.now() - timedelta(days=1)).date()
    
    values = []
    for _, row in df.iterrows():
        values.append(f"({row['kendra_id']}, '{row['plate']}', '{row['status']}', '{row['date']}', {row['company_id']}, {row['center_id']}, {row['manager_id']})")

    values_string = ', '.join(values)
    query = f"""
    INSERT INTO Vehicles (kendra_id, plate, status, date, company_id, center_id, manager_id)
        VALUES {values_string}
        ON DUPLICATE KEY UPDATE
        kendra_id = VALUES(kendra_id),
        plate = VALUES(plate),
        status = VALUES(status),
        date = VALUES(date),
        company_id = VALUES(company_id),
        center_id = VALUES(center_id),
        manager_id = VALUES(manager_id);
    """
    try:
        cursor.execute(query)
        con.commit()
        print(f"Successful insertion of {len(df)} rows into Vehicles table.")
    except mysql.connector.Error as e:
        print(f"Error executing query: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    df = get_vehicle_stati()
    insert_vehicle_data(df)
