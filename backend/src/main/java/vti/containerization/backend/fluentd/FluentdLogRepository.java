package vti.containerization.backend.fluentd;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface FluentdLogRepository extends JpaRepository<FluentdLogModel, Long> {
}
