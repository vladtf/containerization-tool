package vti.containerization.backend.forwarding;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;
import vti.containerization.backend.kafka.KafkaForwardingRulesConsumer;
import vti.containerization.backend.kafka.KafkaForwardingRulesProducer;

import java.util.List;

@Service
@AllArgsConstructor
public class ForwardingService {

    private final KafkaForwardingRulesConsumer kafkaForwardingRulesConsumer;

    private final KafkaForwardingRulesProducer kafkaForwardingRulesProducer;


    public List<ForwardingChainModel> getAllForwardingChains() {
        return kafkaForwardingRulesConsumer.getForwardingChains();
    }

    @SneakyThrows
    public void addForwardingRuleToChain(ForwardingController.AddForwardingRuleRequest forwardingChainModel) {
        ObjectMapper objectMapper = new ObjectMapper();
        String message = objectMapper.writeValueAsString(forwardingChainModel);
        kafkaForwardingRulesProducer.sendForwardingRules("add-forwarding-rules", message);
    }
}
