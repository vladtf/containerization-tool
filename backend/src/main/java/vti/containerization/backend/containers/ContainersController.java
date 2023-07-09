package vti.containerization.backend.containers;


import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/containers")
@AllArgsConstructor
@Log
public class ContainersController {

    private final ContainersService containersService;

    @GetMapping("/all")
    public List<ContainerDataModel> getAllContainers() {
        return containersService.getAllContainers();
    }


}
