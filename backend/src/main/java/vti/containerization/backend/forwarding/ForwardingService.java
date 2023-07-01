package vti.containerization.backend.forwarding;

import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import vti.containerization.backend.kafka.KafkaForwardingRulesConsumer;

import java.util.List;

@Service
@AllArgsConstructor
public class ForwardingService {

    private final KafkaForwardingRulesConsumer kafkaForwardingRulesConsumer;


    public List<ForwardingChainModel> getAllForwardingChains() {
        return kafkaForwardingRulesConsumer.getForwardingChains();
    }
}
