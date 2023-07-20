package vti.containerization.backend.fluentd;

import lombok.AllArgsConstructor;
import lombok.extern.java.Log;
import org.springframework.data.domain.Page;
import org.springframework.web.bind.annotation.*;

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

    @GetMapping("/logs/{ident}")
    public Page<FluentdLogModel> getLogsByIdent(
            @PathVariable String ident,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        return fluentdLogService.getLogsByIdent(ident, page, pageSize);
    }}
