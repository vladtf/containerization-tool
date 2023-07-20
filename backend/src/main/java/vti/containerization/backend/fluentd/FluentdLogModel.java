package vti.containerization.backend.fluentd;


import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "fluentd_logs")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class FluentdLogModel {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "time")
    private LocalDateTime time;

    @Column(name = "host")
    private String host;

    @Column(name = "ident")
    private String ident;

    @Column(name = "pid")
    private Integer pid;

    @Column(name = "msgid")
    private String msgid;

    @Column(name = "extradata")
    private String extradata;

    @Column(name = "message", columnDefinition = "TEXT")
    private String message;

}
