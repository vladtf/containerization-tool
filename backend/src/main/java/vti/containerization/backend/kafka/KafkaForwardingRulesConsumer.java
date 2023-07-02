package vti.containerization.backend.kafka;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import vti.containerization.backend.forwarding.ForwardingChainModel;
import vti.containerization.backend.forwarding.ForwardingRuleModel;

import java.util.*;
import java.util.logging.Logger;

@Component
public class KafkaForwardingRulesConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaForwardingRulesConsumer.class.getName());

    private List<ForwardingChainModel> forwardingChainModels;
    private Timer bufferTimer;
    private Timer logToConsoleTimer;

    private List<ForwardingChainModel> deserializeForwardingChains(String json) {
        try {
            List<ForwardingChainModel> forwardingChainModels = new ArrayList<ForwardingChainModel>();

            // deserialize the json into JsonNode
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(json);

            // get iterator to all the keys in the json
            Iterator<Map.Entry<String, JsonNode>> fieldsIterator = root.fields();

            // iterate through all the keys
            while (fieldsIterator.hasNext()) {
                Map.Entry<String, JsonNode> field = fieldsIterator.next();
                String key = field.getKey();

                List<ForwardingRuleModel> rules = new ArrayList<ForwardingRuleModel>();

                Iterator<Map.Entry<String, JsonNode>> fields = field.getValue().fields();
                while (fields.hasNext()) {
                    Map.Entry<String, JsonNode> rule = fields.next();
                    String ruleKey = rule.getKey();

                    JsonNode ruleValue = rule.getValue();

                    String target = ruleValue.get("target").asText();
                    String protocol = ruleValue.get("protocol").asText();
                    String options = ruleValue.get("options").asText();
                    String source = ruleValue.get("source").asText();
                    String destination = ruleValue.get("destination").asText();
                    String[] extra = mapper.convertValue(ruleValue.get("extra"), String[].class);

                    ForwardingRuleModel forwardingRuleModel = new ForwardingRuleModel(ruleKey, target, protocol, options, source, destination, extra);
                    rules.add(forwardingRuleModel);
                }

                ForwardingChainModel forwardingChainModel = new ForwardingChainModel(key, rules);
                forwardingChainModels.add(forwardingChainModel);
            }

            return forwardingChainModels;
        } catch (Exception e) {
            LOGGER.severe("Failed to deserialize forwarding rules: " + e.getMessage());
            return new ArrayList<ForwardingChainModel>();
        }
    }

    @KafkaListener(topics = "monitor-forwarding-rules", groupId = "my_group")
    public void listen(String message) {
        LOGGER.info("Received forwarding rules from Kafka");

        List<ForwardingChainModel> forwardingRules = deserializeForwardingChains(message);

        if (forwardingRules.size() > 0) {
            this.forwardingChainModels = forwardingRules;
        }

    }

    public List<ForwardingChainModel> getForwardingChains() {
        return forwardingChainModels;
    }
}