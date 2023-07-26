package vti.containerization.backend.upload;

import aj.org.objectweb.asm.ClassReader;
import lombok.AllArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.java.Log;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import vti.containerization.backend.configuration.ContainerizationToolProperties;
import vti.containerization.backend.upload.jar.JarInfoResponse;
import vti.containerization.backend.upload.jar.MainClassVisitor;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.jar.*;

import static vti.containerization.backend.utils.FileUtils.generateUniqueFileName;

@AllArgsConstructor
@Service
@Log
public class UploadArtifactService {

    private final ContainerizationToolProperties containerizationToolProperties;


    @SneakyThrows
    public void handleArtifactUpload(MultipartFile multipartFile) {
        Path tempFile = Files.createTempFile("upload-", multipartFile.getOriginalFilename());
        multipartFile.transferTo(tempFile.toFile());

        handleArtifactUpload(tempFile.toFile());

        // Clean up the temporary file
        Files.delete(tempFile);
    }

    @SneakyThrows
    public void handleArtifactUpload(File file) {
        log.info("Received file: " + file.getName());

        // Get the list of already uploaded files
        List<UploadedFileModel> uploadedFiles = getUploadedFiles();

        // Generate a unique filename
        String fileName = generateUniqueFileName(file.getName(), uploadedFiles);

        log.info(MessageFormat.format("Saving file {0} to {1}", file.getName(), fileName));

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
        Files.copy(file.toPath(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        log.info("File saved to: " + targetPath.toAbsolutePath());
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
                try (JarInputStream jarInputStream = new JarInputStream(new FileInputStream(file))) {
                    Manifest manifest = jarInputStream.getManifest();
                    String mainClassNameFromManifest = getMainClassNameFromManifest(manifest);
                    uploadedFileModel.setJavaMainClass(mainClassNameFromManifest);
                }
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


    public JarInfoResponse getJarInfo(MultipartFile jar) {
        try (JarInputStream jarInputStream = new JarInputStream(jar.getInputStream())) {
            JarInfoResponse response = new JarInfoResponse();

            // Check if the JAR contains a Manifest file
            Manifest manifest = jarInputStream.getManifest();

            String mainClassNameFromManifest = getMainClassNameFromManifest(manifest);
            response.setMainClassName(mainClassNameFromManifest);

            response.setClassesWithMainMethod(scanForClassesWithMain(jarInputStream));
            return response;
        } catch (IOException e) {
            // Handle any potential IOException here
            e.printStackTrace();
            // You may also set an error flag in the response or throw a custom exception
        }

        throw new RuntimeException("Failed to get JAR info");
    }

    private String getMainClassNameFromManifest(Manifest manifest) throws IOException {
        if (manifest == null) {
            return null;
        }

        Attributes attributes = manifest.getMainAttributes();
        return attributes.getValue("Main-Class");
    }

    private List<String> scanForClassesWithMain(JarInputStream jarInputStream) throws IOException {
        List<String> classesWithMain = new ArrayList<>();

        JarEntry entry;
        while ((entry = jarInputStream.getNextJarEntry()) != null) {
            if (!entry.isDirectory() && entry.getName().endsWith(".class")) {
                ClassReader classReader = new ClassReader(jarInputStream);
                MainClassVisitor visitor = new MainClassVisitor();
                classReader.accept(visitor, ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
                if (visitor.hasMainMethod()) {
                    classesWithMain.add(visitor.getClassName());
                }
            }
        }

        return classesWithMain;
    }

    @SneakyThrows
    public void handleJarUpload(MultipartFile file, String selectedMainClass) {
        JarInfoResponse jarInfo = getJarInfo(file);

        if (jarInfo.getMainClassName() != null && jarInfo.getMainClassName().equals(selectedMainClass)) {
            handleArtifactUpload(file);
            return;
        }

        if (!jarInfo.getClassesWithMainMethod().contains(selectedMainClass)) {
            throw new RuntimeException("The selected main class doesn't contain a main method");
        }

        // Save the uploaded file to a temporary location
        Path tempDir = Files.createTempDirectory("uploaded-jar");
        Path jarPath = tempDir.resolve(file.getOriginalFilename());
        Files.copy(file.getInputStream(), jarPath, StandardCopyOption.REPLACE_EXISTING);

        try (JarFile jar = new JarFile(jarPath.toFile())) {
            // Load the JAR file and get the manifest
            Manifest manifest = jar.getManifest();

            // Update the Main-Class attribute in the manifest
            manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS, selectedMainClass);

            // Create an in-memory buffer to store the updated JAR
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            try (JarOutputStream jos = new JarOutputStream(baos, manifest)) {
                for (JarEntry entry : Collections.list(jar.entries())) {
                    if (!entry.getName().equalsIgnoreCase("META-INF/MANIFEST.MF")) {
                        try (InputStream is = jar.getInputStream(entry)) {
                            jos.putNextEntry(new JarEntry(entry.getName()));
                            byte[] buffer = new byte[1024];
                            int bytesRead;
                            while ((bytesRead = is.read(buffer)) != -1) {
                                jos.write(buffer, 0, bytesRead);
                            }
                            jos.flush();
                            jos.closeEntry();
                        }
                    }
                }
            }

            // Save the updated JAR to disk
            Files.write(jarPath, baos.toByteArray());

            // Now handle the updated JAR file
            File updatedJarFile = jarPath.toFile();
            handleArtifactUpload(updatedJarFile);
        }

        // Clean up the temporary file
        Files.delete(jarPath);
    }
}
