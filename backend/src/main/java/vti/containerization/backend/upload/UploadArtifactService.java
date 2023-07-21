package vti.containerization.backend.upload;

import static vti.containerization.backend.utils.FileUtils.generateUniqueFileName;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import vti.containerization.backend.configuration.ContainerizationToolProperties;

@AllArgsConstructor
@Service
@Log
public class UploadArtifactService {

    private final ContainerizationToolProperties containerizationToolProperties;


    public void handleArtifactUpload(MultipartFile file) throws IOException {
        log.info("Received file: " + file.getOriginalFilename());

        // Get the list of already uploaded files
        List<UploadedFileModel> uploadedFiles = getUploadedFiles();

        // Generate a unique filename
        String fileName = generateUniqueFileName(Objects.requireNonNull(file.getOriginalFilename()), uploadedFiles);

        log.info(MessageFormat.format("Saving file {0} to {1}", file.getOriginalFilename(), fileName));

        // Create the target directory if it doesn't exist
        File targetDirectory = new File(containerizationToolProperties.getUpload().getDirectory());
        if (!targetDirectory.exists()) {
            boolean mkdirs = targetDirectory.mkdirs();
            if (!mkdirs) {
                throw new RuntimeException("Failed to create the target directory: " + targetDirectory.getAbsolutePath());
            }
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

    public void deleteUploadedFile(String fileName) {
        log.info("Deleting file: " + fileName);

        File targetDirectory = new File(containerizationToolProperties.getUpload().getDirectory());
        File[] files = targetDirectory.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.getName().equals(fileName)) {
                    boolean delete = file.delete();

                    if (delete) {
                        log.info("File deleted successfully: " + file.getAbsolutePath());
                    } else {
                        log.info("Failed to delete the file: " + file.getAbsolutePath());
                        throw new RuntimeException("Failed to delete the file: " + file.getAbsolutePath());
                    }
                }
            }
        }
    }
}
