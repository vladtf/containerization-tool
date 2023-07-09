package vti.containerization.backend.containers;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@AllArgsConstructor
@Log
public class ContainersService {
    public List<ContainerDataModel> getAllContainers() {
        return null;
    }
}
