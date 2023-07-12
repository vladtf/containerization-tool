package vti.containerization.backend.utils;

import vti.containerization.backend.upload.UploadedFileModel;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

public final class FileUtils {

    private FileUtils() {
        throw new IllegalStateException("Utility class");
    }

    public static String generateUniqueFileName(String fileName, List<UploadedFileModel> uploadedFiles) {
        Set<String> existingFileNames = uploadedFiles.stream()
                .map(UploadedFileModel::getName)
                .collect(Collectors.toSet());

        int dotIndex = fileName.lastIndexOf(".");
        String nameWithoutExtension = dotIndex != -1 ? fileName.substring(0, dotIndex) : fileName;
        String extension = dotIndex != -1 ? fileName.substring(dotIndex) : "";

        String uniqueFileName = fileName;
        int i = 1;
        while (existingFileNames.contains(uniqueFileName)) {
            uniqueFileName = nameWithoutExtension + "_" + i + extension;
            i++;
        }

        return uniqueFileName;
    }
}
