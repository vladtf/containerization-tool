package vti.containerization.backend.fluentd;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/fluentd")
@AllArgsConstructor
@Log
public class FluentdLogController {
    private final FluentdLogService fluentdLogService;

    @GetMapping("/logs")
    public List<FluentdLogModel> getAllLogs() {
        return fluentdLogService.getAllLogs();
    }
}
