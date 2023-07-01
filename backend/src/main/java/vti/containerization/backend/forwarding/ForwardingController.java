package vti.containerization.backend.forwarding;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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

}
