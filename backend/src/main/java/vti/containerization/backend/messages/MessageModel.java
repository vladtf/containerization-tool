package vti.containerization.backend.messages;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
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
