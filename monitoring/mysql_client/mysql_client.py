from flask_mysqldb import MySQL

from azure_client.azure_client import AzureContainer


def get_all_azure_containers(mysql: MySQL) -> list[AzureContainer]:
    query = "SELECT * FROM azure_container"

    cursor = mysql.connection.cursor()

    cursor.execute(query)

    # Fetch the column names
    column_names = [desc[0] for desc in cursor.description]

    # Fetch all rows in the result set
    result = cursor.fetchall()

    # Create a list of dictionaries, where each dictionary represents a row
    # The keys in the dictionary are the column names, and the values are the corresponding cell values in the row
    azure_containers = [AzureContainer.from_dict(dict(zip(column_names, row))) for row in result]

    cursor.close()

    return azure_containers


def get_azure_container_by_id(mysql: MySQL, container_id: str) -> AzureContainer:
    query = "SELECT * FROM azure_container WHERE id = %s"

    cursor = mysql.connection.cursor()

    cursor.execute(query, (container_id,))

    result = cursor.fetchone()

    azure_container = AzureContainer(*result)

    cursor.close()

    return azure_container


def get_azure_container_by_name(mysql: MySQL, container_name: str) -> AzureContainer:
    query = "SELECT * FROM azure_container WHERE name = %s"

    cursor = mysql.connection.cursor()

    cursor.execute(query, (container_name,))

    result = cursor.fetchone()

    azure_container = AzureContainer(*result)

    cursor.close()

    return azure_container


def azure_container_exists_by_name(mysql: MySQL, container_name: str) -> bool:
    query = "SELECT * FROM azure_container WHERE name = %s"

    cursor = mysql.connection.cursor()

    cursor.execute(query, (container_name,))

    result = cursor.fetchone()

    cursor.close()

    return result is not None


def delete_azure_container_by_id(mysql: MySQL, container_id: str):
    query = "DELETE FROM azure_container WHERE id = %s"

    cursor = mysql.connection.cursor()

    cursor.execute(query, (container_id,))

    mysql.connection.commit()

    cursor.close()


def insert_azure_container(mysql: MySQL, azure_container: AzureContainer):
    query = ("INSERT INTO azure_container "
             "(name, status, image, instance_id, instance_name) "
             "VALUES (%s, %s, %s, %s, %s)")

    cursor = mysql.connection.cursor()

    cursor.execute(query, (azure_container.name, azure_container.status, azure_container.image,
                           azure_container.instance_id, azure_container.instance_name))

    mysql.connection.commit()

    cursor.close()


def update_azure_container(mysql: MySQL, azure_container: AzureContainer):
    query = ("UPDATE azure_container "
             "SET status = %s, image = %s, instance_id = %s, instance_name = %s "
             "WHERE id = %s")

    cursor = mysql.connection.cursor()

    cursor.execute(query, (azure_container.status, azure_container.image, azure_container.instance_id,
                           azure_container.instance_name, azure_container.id))

    mysql.connection.commit()

    cursor.close()
