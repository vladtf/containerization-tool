package vti.containerization.backend.fluentd;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FluentdLogRepository extends JpaRepository<FluentdLogModel, Long> {
    Page<FluentdLogModel> findByIdent(String ident, Pageable pageable);
}
