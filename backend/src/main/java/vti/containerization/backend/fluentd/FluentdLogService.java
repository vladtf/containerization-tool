package vti.containerization.backend.fluentd;

import io.micrometer.common.util.StringUtils;
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

    public List<FluentdLogModel> getLogsByIdent(String ident) {
        // if containerId is bigger than 12 characters then take first 12 characters
        if (StringUtils.isBlank(ident)) {
            throw new RuntimeException("Ident cannot be null or empty");
        }

        if (ident.length() < 12) {
            throw new RuntimeException("Ident cannot be less than 12 characters");
        }

        ident = ident.substring(0, 12);

        return fluentdLogRepository.findByIdent(ident);
    }
}
