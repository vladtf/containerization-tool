package vti.containerization.backend.upload.jar;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;


@Data
@AllArgsConstructor
@NoArgsConstructor
public class JarInfoResponse {
    private String mainClassName;
    private List<String> classesWithMainMethod;

}

