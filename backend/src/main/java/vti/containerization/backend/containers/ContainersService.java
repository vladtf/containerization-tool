package vti.containerization.backend.containers;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.stereotype.Service;
import vti.containerization.backend.kafka.KafkaContainersDataConsumer;

import java.util.List;

@Service
@AllArgsConstructor
@Log
public class ContainersService {

    private final KafkaContainersDataConsumer kafkaContainersDataConsumer;

    public List<ContainerDataModel> getAllContainers() {
        return kafkaContainersDataConsumer.getContainersData();
    }
}
