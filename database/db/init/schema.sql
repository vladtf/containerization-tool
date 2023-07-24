USE localdb;

CREATE TABLE
    containers (
        id VARCHAR(12) PRIMARY KEY,
        name VARCHAR(255),
        status VARCHAR(50),
        ip VARCHAR(20),
        image VARCHAR(255),
        created DATETIME
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
CREATE PROCEDURE InsertContainerIfMissing(IN container_id VARCHAR(12))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM containers WHERE id = container_id) THEN
        INSERT INTO containers (id) VALUES (container_id);
    END IF;
END//
DELIMITER ;


CREATE TRIGGER BeforeInsertFluentdLog
BEFORE INSERT ON fluentd_logs
FOR EACH ROW
BEGIN
    CALL InsertContainerIfMissing(NEW.ident);
END;
