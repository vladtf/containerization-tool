package vti.containerization.backend.containers;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "containers")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class ContainerDataModel {

    @Id
    private String id;
    private String name;
    private String status;
    private String ip;
    private String image;
    private LocalDateTime created;
}
