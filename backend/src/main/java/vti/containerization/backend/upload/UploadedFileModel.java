package vti.containerization.backend.upload;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.core.annotation.AliasFor;

import java.io.File;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UploadedFileModel {
    private String name;
    private FileType type;
    private String size;
    private String path;

    public enum FileType {
        JAR, ZIP, WAR, SHELL, UNKNOWN;

        public static FileType fromFile(File file) {
            String fileName = file.getName();
            if (fileName.endsWith(".jar")) {
                return JAR;
            } else if (fileName.endsWith(".zip")) {
                return ZIP;
            } else if (fileName.endsWith(".war")) {
                return WAR;
            } else if (fileName.endsWith(".sh")) {
                return SHELL;
            } else {
                return UNKNOWN;
            }
        }
    }
}
