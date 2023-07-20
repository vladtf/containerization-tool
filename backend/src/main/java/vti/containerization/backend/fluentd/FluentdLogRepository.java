package vti.containerization.backend.fluentd;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FluentdLogRepository extends JpaRepository<FluentdLogModel, Long> {
    List<FluentdLogModel> findByIdent(String ident);
}
