package vti.containerization.backend.upload;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.FileCopyUtils;
import org.springframework.web.multipart.MultipartFile;
import vti.containerization.backend.configuration.ContainerizationToolProperties;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
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
}
