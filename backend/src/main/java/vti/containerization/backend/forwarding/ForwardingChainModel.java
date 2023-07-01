package vti.containerization.backend.forwarding;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ForwardingChainModel {
    private String name;
    private List<ForwardingRuleModel> rules;
}
