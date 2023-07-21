package vti.containerization.backend.upload;

import java.io.File;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

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
