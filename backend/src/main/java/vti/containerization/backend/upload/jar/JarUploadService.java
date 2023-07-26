package vti.containerization.backend.upload.jar;

import aj.org.objectweb.asm.ClassReader;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.jar.*;

@Service
public class JarUploadService {

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
            throw new RuntimeException("Failed to get JAR info", e);
        }
    }

    @SneakyThrows
    public File buildJarToUpload(MultipartFile file, String selectedMainClass) {
        JarInfoResponse jarInfo = getJarInfo(file);

        if (isMainClassExisting(jarInfo, selectedMainClass)) {
            // No need to update the JAR, return the original file directly
            return fileToTempFile(file);
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

            // Update jar with the new manifest
            updateJarWithNewManifest(jar, manifest, jarPath);

            // Return the updated JAR file
            return jarPath.toFile();
        } catch (IOException e) {
            // Handle any potential IOException here
            e.printStackTrace();
            // You may also set an error flag in the response or throw a custom exception
            throw new RuntimeException("Failed to build JAR", e);
        }
    }

    public String getMainClassNameFromManifest(Manifest manifest) {
        if (manifest == null) {
            return null;
        }
        Attributes attributes = manifest.getMainAttributes();
        return attributes.getValue(Attributes.Name.MAIN_CLASS);
    }

    @SneakyThrows
    public String getMainClassNameFromManifest(File file) {
        try (JarInputStream jarInputStream = new JarInputStream(new FileInputStream(file))) {
            Manifest manifest = jarInputStream.getManifest();
            return getMainClassNameFromManifest(manifest);
        }
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

    private boolean isMainClassExisting(JarInfoResponse jarInfo, String selectedMainClass) {
        return jarInfo.getMainClassName() != null && jarInfo.getMainClassName().equals(selectedMainClass);
    }

    // Helper method to convert MultipartFile to temporary File
    private File fileToTempFile(MultipartFile file) throws IOException {
        File tempFile = File.createTempFile("uploaded-jar", file.getOriginalFilename());
        try (InputStream inputStream = file.getInputStream();
             OutputStream outputStream = new FileOutputStream(tempFile)) {
            byte[] buffer = new byte[1024];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }
        }
        return tempFile;
    }

    @SneakyThrows
    private void updateJarWithNewManifest(JarFile jar, Manifest manifest, Path jarPath) {
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
    }
}
