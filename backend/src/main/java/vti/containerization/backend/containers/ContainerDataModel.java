package vti.containerization.backend.containers;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ContainerDataModel {
    private String id;
    private String name;
    private String status;
    private String ip;
}
