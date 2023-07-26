package vti.containerization.backend.upload;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import vti.containerization.backend.upload.jar.JarInfoResponse;
import vti.containerization.backend.upload.jar.JarUploadService;

import java.util.List;

@RestController
@RequestMapping("/upload")
@AllArgsConstructor
@Log
public class UploadArtifactController {

    private final UploadArtifactService uploadArtifactService;
    private final JarUploadService jarUploadService;

    @PostMapping
    public ResponseEntity<String> uploadArtifact(@RequestParam("file") MultipartFile file) {
        try {
            uploadArtifactService.handleArtifactUpload(file);
            return ResponseEntity.ok("File uploaded successfully!");
        } catch (Exception e) {
            log.log(java.util.logging.Level.SEVERE, "Failed to upload the file: " + e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to upload the file: " + e.getMessage());
        }
    }

    @PostMapping("/jar/info")
    public ResponseEntity<JarInfoResponse> getJarInfo(@RequestParam("file") MultipartFile file) {
        try {
            JarInfoResponse jarInfo = jarUploadService.getJarInfo(file);
            return ResponseEntity.ok(jarInfo);
        } catch (Exception e) {
            log.log(java.util.logging.Level.SEVERE, "Failed to upload the file: " + e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(null);
        }
    }

    @PostMapping("/jar")
    public ResponseEntity<String> uploadJar(@RequestParam("file") MultipartFile file, @RequestParam String selectedMainClass) {
        try {
            uploadArtifactService.handleJarUpload(file, selectedMainClass);
            return ResponseEntity.ok("File uploaded successfully!");
        } catch (Exception e) {
            log.log(java.util.logging.Level.SEVERE, "Failed to upload the file: " + e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to upload the file: " + e.getMessage());
        }
    }

    @GetMapping("/files")
    public ResponseEntity<List<UploadedFileModel>> getUploadedFiles() {
        try {
            List<UploadedFileModel> uploadedFiles = uploadArtifactService.getUploadedFiles();
            return ResponseEntity.ok(uploadedFiles);
        } catch (Exception e) {
            log.log(java.util.logging.Level.SEVERE, "Failed to retrieve uploaded files: " + e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(null);
        }
    }

    @DeleteMapping("/files/{fileName}")
    public ResponseEntity<String> deleteUploadedFile(@PathVariable String fileName) {
        try {
            uploadArtifactService.deleteUploadedFile(fileName);
            return ResponseEntity.ok("File deleted successfully!");
        } catch (Exception e) {
            log.log(java.util.logging.Level.SEVERE, "Failed to delete the file: " + e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to delete the file: " + e.getMessage());
        }
    }

}
