package vti.containerization.backend.traffic;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class MessageModel {
    private String protocol;

    @JsonProperty("src_ip")
    private String source;

    @JsonProperty("dst_ip")
    private String destination;

    @JsonProperty("src_port")
    private String sourcePort;

    @JsonProperty("dst_port")
    private String destinationPort;
}
