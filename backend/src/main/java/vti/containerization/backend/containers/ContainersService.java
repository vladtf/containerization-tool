package vti.containerization.backend.containers;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.stereotype.Service;
import vti.containerization.backend.kafka.KafkaContainersDataConsumer;
import vti.containerization.backend.kafka.KafkaContainersDataProducer;
import vti.containerization.backend.kafka.KafkaContainersErrorConsumer;
import vti.containerization.backend.upload.UploadArtifactService;
import vti.containerization.backend.upload.UploadedFileModel;

import java.util.List;

@Service
@AllArgsConstructor
@Log
public class ContainersService {
    private final KafkaContainersErrorConsumer kafkaContainersErrorConsumer;

    private final KafkaContainersDataConsumer kafkaContainersDataConsumer;
    private final KafkaContainersDataProducer kafkaContainersDataProducer;
    private final UploadArtifactService uploadArtifactService;

    public List<ContainerDataModel> getAllContainers() {
        return kafkaContainersDataConsumer.getContainersData();
    }

    public void createContainer(ContainersController.CreateContainerRequest request) {
        UploadedFileModel uploadedFile = uploadArtifactService.getUploadedFileByName(request.getFileId())
                .orElseThrow(() -> new RuntimeException("File not found"));

        request.setContainerName("container-" + request.getFileId());
        request.setFilePath("/" + uploadedFile.getPath());

        kafkaContainersDataProducer.sendCreateContainerRequest(request);
        log.info("Container created successfully");
    }

    public void deleteContainer(String containerId) {
        kafkaContainersDataProducer.sendDeleteContainerRequest(containerId);
        log.info("Container deleted successfully");
    }

    public List<String> getErrors() {
        return kafkaContainersErrorConsumer.getErrors();
    }
}
