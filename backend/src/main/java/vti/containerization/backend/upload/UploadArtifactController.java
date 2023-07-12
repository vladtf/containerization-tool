package vti.containerization.backend.upload;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/upload")
@AllArgsConstructor
@Log
public class UploadArtifactController {

    private final UploadArtifactService uploadArtifactService;

    @PostMapping
    public ResponseEntity<String> uploadArtifact(@RequestParam("file") MultipartFile file) {
        try {
            // Invoke your service to handle the uploaded file, e.g., store it in Azure Blob storage
            uploadArtifactService.handleArtifactUpload(file);
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
