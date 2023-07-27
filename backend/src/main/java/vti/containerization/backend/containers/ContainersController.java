package vti.containerization.backend.containers;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.web.bind.annotation.*;
import vti.containerization.backend.kafka.entities.KafkaFeedbackMessage;

import java.util.List;

@RestController
@RequestMapping("/containers")
@AllArgsConstructor
@Log
public class ContainersController {

    private final ContainersService containersService;

    @GetMapping
    public List<ContainerDataModel> getAllContainers() {
        return containersService.getAllContainers();
    }

    @PostMapping("/create")
    public void createContainer(@RequestBody CreateContainerRequest request) {
        // You can implement the logic to create a container here using the data from the request
        containersService.createContainer(request);
        log.info("Container created successfully");
    }

    @PostMapping("/deploy")
    public String deployContainer(@RequestBody CreateContainerRequest request) {
        // You can implement the logic to create a container here using the data from the request
        return containersService.deployContainer(request);
    }

    @DeleteMapping("/{containerId}")
    public void deleteContainer(@PathVariable String containerId) {
        // You can implement the logic to delete a container here using the provided containerId
        containersService.deleteContainer(containerId);
        log.info("Container deleted successfully");
    }

    @GetMapping("/feedback")
    public List<KafkaFeedbackMessage> getFeedback() {
        return containersService.getFeedback();
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class CreateContainerRequest {
        private String fileId;
        private String filePath;
        private String containerName;
        private String fileType;
    }
}
