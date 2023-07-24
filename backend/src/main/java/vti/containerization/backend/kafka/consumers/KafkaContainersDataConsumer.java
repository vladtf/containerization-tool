package vti.containerization.backend.kafka.consumers;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import vti.containerization.backend.containers.ContainerDataModel;
import vti.containerization.backend.containers.ContainerDataRepository;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

@Component
@AllArgsConstructor
@Log
public class KafkaContainersDataConsumer {

    private List<ContainerDataModel> containersData;

    private final ContainerDataRepository containerDataRepository;

    private final ObjectMapper objectMapper;


    private List<ContainerDataModel> deserializeMessage(String json) {
        try {
            ContainerDataModel[] containerDataModels = objectMapper.readValue(json, ContainerDataModel[].class);
            return Arrays.asList(containerDataModels);
        } catch (JsonProcessingException e) {
            log.warning("Failed to deserialize message: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    private void saveToDatabase(List<ContainerDataModel> containersData) {
        containerDataRepository.saveAll(containersData);
    }

    @KafkaListener(topics = "containers-data", groupId = "my_group")
    public void listen(String message) {
        log.info("Received containers data: " + message);
        this.containersData = deserializeMessage(message);

        saveToDatabase(this.containersData);
    }

    public List<ContainerDataModel> getContainersData() {
        return containersData;
    }
}
