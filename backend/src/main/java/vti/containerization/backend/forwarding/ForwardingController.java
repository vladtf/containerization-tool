package vti.containerization.backend.forwarding;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.bind.annotation.*;
import vti.containerization.backend.kafka.entities.KafkaFeedbackMessage;

import java.util.List;

@RestController
@RequestMapping("/forwarding-chains")
@AllArgsConstructor
public class ForwardingController {

    private final ForwardingService forwardingService;

    @GetMapping("/all")
    public List<ContainerForwardingRulesModel> getAllForwardingChains() {
        return forwardingService.getAllForwardingChains();
    }


    @PostMapping("/add")
    public void addForwardingRuleToChain(@RequestBody AddForwardingRuleRequest forwardingChainModel) {
        forwardingService.addForwardingRuleToChain(forwardingChainModel);
    }

    @PostMapping("/clear")
    public void clearForwardingRules(@RequestBody ClearForwardingRulesRequest request) {
        forwardingService.clearForwardingRules(request);
    }

    @GetMapping("/feedback")
    public List<KafkaFeedbackMessage> getFeedback() {
        return forwardingService.getFeedback();
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class AddForwardingRuleRequest {
        private String chainName;
        private String containerId;
        private ForwardingRuleModel rule;
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class ClearForwardingRulesRequest {
        private String containerId;
    }

}
