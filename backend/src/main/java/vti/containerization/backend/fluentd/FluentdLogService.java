package vti.containerization.backend.fluentd;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@AllArgsConstructor
@Log
public class FluentdLogService {
    private final FluentdLogRepository fluentdLogRepository;

    public List<FluentdLogModel> getAllLogs() {
        return fluentdLogRepository.findAll();
    }
}
