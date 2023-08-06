USE localdb;

CREATE TABLE
    containers (
        id VARCHAR(12) PRIMARY KEY,
        name VARCHAR(255) UNIQUE,
        status VARCHAR(50),
        ip VARCHAR(20),
        image VARCHAR(255),
        created DATETIME
    );

CREATE TABLE
    azure_container (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) UNIQUE,
        status VARCHAR(50),
        image VARCHAR(255),
        instance_id VARCHAR(255),
        instance_name VARCHAR(255)
    );

CREATE TABLE
    fluentd_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        time DATETIME,
        host VARCHAR(255),
        ident VARCHAR(12),
        pid INT,
        msgid VARCHAR(255),
        extradata VARCHAR(255),
        message TEXT,
        FOREIGN KEY (ident) REFERENCES containers (id) ON DELETE CASCADE
    );

# A procedure to insert a container if it doesn't exist 

DELIMITER //

CREATE PROCEDURE INSERTCONTAINERIFMISSING(IN CONTAINER_ID 
VARCHAR(12)) BEGIN 
	IF NOT EXISTS (
	    SELECT 1
	    FROM containers
	    WHERE
	        id = container_id
	) THEN
	INSERT INTO containers (id)
	VALUES (container_id);
	END IF;
	END// 


DELIMITER ;

CREATE TRIGGER BEFOREINSERTFLUENTDLOG BEFORE INSERT 
ON FLUENTD_LOGS FOR EACH ROW BEGIN 
	CALL InsertContainerIfMissing(NEW.ident);
END; 

# A trigger to prevent updating a container with status 'deleted'

DELIMITER //

CREATE TRIGGER BEFOREUPDATECONTAINERS BEFORE UPDATE 
ON CONTAINERS FOR EACH ROW BEGIN 
	IF OLD.status = 'deleted' THEN -- Prevent updating if the current status is 'deleted'
	SIGNAL SQLSTATE '45000'
	SET
	    MESSAGE_TEXT = 'Updates not allowed for rows with status "deleted".';
	END IF;
END; 

// 

DELIMITER ;