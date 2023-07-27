package vti.containerization.backend.upload;

import lombok.AllArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.java.Log;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import vti.containerization.backend.configuration.ContainerizationToolProperties;
import vti.containerization.backend.upload.jar.JarInfoResponse;
import vti.containerization.backend.upload.jar.JarUploadService;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static vti.containerization.backend.utils.FileUtils.generateUniqueFileName;

@AllArgsConstructor
@Service
@Log
public class UploadArtifactService {

    private final ContainerizationToolProperties containerizationToolProperties;
    private final JarUploadService jarUploadService;


    @SneakyThrows
    public void handleArtifactUpload(MultipartFile multipartFile) {
        Path tempFile = Files.createTempFile("upload-", multipartFile.getOriginalFilename());
        multipartFile.transferTo(tempFile.toFile());

        handleArtifactUpload(tempFile.toFile(), multipartFile.getOriginalFilename());

        // Clean up the temporary file
        Files.delete(tempFile);
    }

    @SneakyThrows
    public void handleArtifactUpload(File file, String originalFileName) {
        log.info("Received file: " + file.getName());

        // Get the list of already uploaded files
        List<UploadedFileModel> uploadedFiles = getUploadedFiles();

        // Generate a unique filename
        String fileName = generateUniqueFileName(originalFileName, uploadedFiles);

        log.info(MessageFormat.format("Saving file {0} to {1}", file.getName(), fileName));

        // Create the target directory if it doesn't exist
        Path targetPath = getPath(fileName);
        Files.copy(file.toPath(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        log.info("File saved to: " + targetPath.toAbsolutePath());
    }

    private Path getPath(String fileName) {
        File targetDirectory = new File(containerizationToolProperties.getUpload().getDirectory());
        if (!targetDirectory.exists()) {
            boolean mkdirs = targetDirectory.mkdirs();
            if (!mkdirs) {
                throw new RuntimeException("Failed to create the target directory: " + targetDirectory.getAbsolutePath());
            }
        }

        // Save the file to the target directory
        return targetDirectory.toPath().resolve(fileName);
    }

    @SneakyThrows
    public List<UploadedFileModel> getUploadedFiles() {
        File targetDirectory = new File(containerizationToolProperties.getUpload().getDirectory());
        File[] files = targetDirectory.listFiles();
        List<UploadedFileModel> uploadedFiles = new ArrayList<>();
        if (files == null) {
            return uploadedFiles;
        }

        for (File file : files) {
            UploadedFileModel uploadedFileModel = new UploadedFileModel();
            uploadedFileModel.setName(file.getName());
            uploadedFileModel.setType(UploadedFileModel.FileType.fromFile(file));
            uploadedFileModel.setSize(String.valueOf(file.length()));
            uploadedFileModel.setPath(file.getAbsolutePath());
            uploadedFiles.add(uploadedFileModel);

            // Get the main class name if the file is a JAR
            if (uploadedFileModel.getType() == UploadedFileModel.FileType.JAR) {
                String mainClassNameFromManifest = jarUploadService.getMainClassNameFromManifest(file);
                uploadedFileModel.setJavaMainClass(mainClassNameFromManifest);
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

    @SneakyThrows
    public void handleJarUpload(MultipartFile multipartFile, String selectedMainClass) {
        File jarUpload = jarUploadService.buildJarToUpload(multipartFile, selectedMainClass);
        handleArtifactUpload(jarUpload, multipartFile.getOriginalFilename());
        Files.deleteIfExists(jarUpload.toPath());
    }

    public JarInfoResponse getJarInfo(MultipartFile file) {
        return jarUploadService.getJarInfo(file);
    }
}
