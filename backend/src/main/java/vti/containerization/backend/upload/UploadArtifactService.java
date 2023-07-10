package vti.containerization.backend.upload;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import vti.containerization.backend.configuration.ContainerizationToolProperties;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@AllArgsConstructor
@Service
@Log
public class UploadArtifactService {

    private final ContainerizationToolProperties containerizationToolProperties;

    public void handleArtifactUpload(MultipartFile file) throws IOException {
        log.info("Received file: " + file.getOriginalFilename());

        // Generate a unique filename
        String fileName = UUID.randomUUID().toString() + "-" + file.getOriginalFilename();

        // Create the target directory if it doesn't exist
        File targetDirectory = new File(containerizationToolProperties.getUpload().getDirectory());
        if (!targetDirectory.exists()) {
            targetDirectory.mkdirs();
        }

        // Save the file to the target directory
        Path targetPath = targetDirectory.toPath().resolve(fileName);
        Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        log.info("File saved to: " + targetPath.toAbsolutePath());
    }


    public List<UploadedFileModel> getUploadedFiles() {
        File targetDirectory = new File(containerizationToolProperties.getUpload().getDirectory());
        File[] files = targetDirectory.listFiles();
        List<UploadedFileModel> uploadedFiles = new ArrayList<>();
        if (files != null) {
            for (File file : files) {
                UploadedFileModel uploadedFileModel = new UploadedFileModel();
                uploadedFileModel.setName(file.getName());
                uploadedFileModel.setType(UploadedFileModel.FileType.fromFile(file));
                uploadedFileModel.setSize(String.valueOf(file.length()));
                uploadedFileModel.setPath(file.getAbsolutePath());
                uploadedFiles.add(uploadedFileModel);
            }
        }

        return uploadedFiles;
    }

    public Optional<UploadedFileModel> getUploadedFileByName(String fileName) {
        List<UploadedFileModel> uploadedFiles = getUploadedFiles();

        for (UploadedFileModel uploadedFile : uploadedFiles) {
            if (uploadedFile.getName().equals(fileName)) {
                return Optional.of(uploadedFile);
            }
        }

        return Optional.empty();
    }

}
