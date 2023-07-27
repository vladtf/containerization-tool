package vti.containerization.backend.containers;

import java.util.List;

import org.springframework.stereotype.Service;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import vti.containerization.backend.kafka.consumers.KafkaContainersDataConsumer;
import vti.containerization.backend.kafka.consumers.KafkaContainersFeedbackConsumer;
import vti.containerization.backend.kafka.entities.KafkaFeedbackMessage;
import vti.containerization.backend.kafka.producers.KafkaContainersDataProducer;
import vti.containerization.backend.upload.UploadArtifactService;
import vti.containerization.backend.upload.UploadedFileModel;

@Service
@AllArgsConstructor
@Log
public class ContainersService {
    private final KafkaContainersFeedbackConsumer kafkaContainersFeedbackConsumer;

    private final KafkaContainersDataConsumer kafkaContainersDataConsumer;
    private final KafkaContainersDataProducer kafkaContainersDataProducer;
    private final UploadArtifactService uploadArtifactService;
    private final ContainerDataRepository containerDataRepository;

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
        containerDataRepository.deleteById(containerId);
        log.info("Container deleted successfully");
    }

    public List<KafkaFeedbackMessage> getFeedback() {
        return kafkaContainersFeedbackConsumer.getFeedbackMessages();
    }

    public String deployContainer(ContainerDataModel container) {
        kafkaContainersDataProducer.sendDeployContainerRequest(container);
        return "Container deployed successfully";
    }
}
