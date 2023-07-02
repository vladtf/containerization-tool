package vti.containerization.backend.forwarding;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/forwarding-chains")
@AllArgsConstructor
public class ForwardingController {

    private final ForwardingService forwardingService;

    @GetMapping("/all")
    public List<ForwardingChainModel> getAllForwardingChains() {
        return forwardingService.getAllForwardingChains();
    }


    @PostMapping("/add")
    public void addForwardingRuleToChain(@RequestBody AddForwardingRuleRequest forwardingChainModel) {
        forwardingService.addForwardingRuleToChain(forwardingChainModel);
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class AddForwardingRuleRequest {
        private String chainName;

        private ForwardingRuleModel rule;
    }

}
