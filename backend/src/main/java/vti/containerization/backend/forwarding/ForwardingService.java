package vti.containerization.backend.forwarding;

import lombok.AllArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;
import vti.containerization.backend.kafka.consumers.KafkaForwardingRulesConsumer;
import vti.containerization.backend.kafka.producers.KafkaForwardingRulesProducer;

import java.util.List;

@Service
@AllArgsConstructor
public class ForwardingService {

    private final KafkaForwardingRulesConsumer kafkaForwardingRulesConsumer;

    private final KafkaForwardingRulesProducer kafkaForwardingRulesProducer;


    public List<ContainerForwardingRulesModel> getAllForwardingChains() {
        return kafkaForwardingRulesConsumer.getForwardingChains();
    }

    @SneakyThrows
    public void addForwardingRuleToChain(ForwardingController.AddForwardingRuleRequest forwardingChainModel) {
        kafkaForwardingRulesProducer.sendForwardingRules(forwardingChainModel);
    }

    @SneakyThrows
    public void clearForwardingRules(ForwardingController.ClearForwardingRulesRequest request) {
        kafkaForwardingRulesProducer.sendClearForwardingRules(request);
    }
}
