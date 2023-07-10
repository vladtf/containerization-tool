package vti.containerization.backend.forwarding;


import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ContainerForwardingRulesModel {
    private String containerId;
    private String containerName;
    private List<ForwardingRuleModel> rules;
}
