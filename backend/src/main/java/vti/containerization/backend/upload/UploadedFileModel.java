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
        JAR(".jar"),
        ZIP(".zip"),
        WAR(".war"),
        SHELL(".sh"),
        PYTHON(".py"),
        UNKNOWN("");

        private final String fileExtension;

        FileType(String fileExtension) {
            this.fileExtension = fileExtension;
        }

        public String getFileExtension() {
            return fileExtension;
        }

        public static FileType fromFile(File file) {
            String fileName = file.getName();
            for (FileType fileType : FileType.values()) {
                if (fileName.endsWith(fileType.getFileExtension())) {
                    return fileType;
                }
            }
            return UNKNOWN;
        }
    }
}
