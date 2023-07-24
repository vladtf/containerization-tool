package vti.containerization.backend.containers;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ContainerDataRepository extends JpaRepository<ContainerDataModel, String> {

    default ContainerDataModel saveIfNotExists(ContainerDataModel containerDataModel) {
        if (existsById(containerDataModel.getId())) {
            return containerDataModel;
        }

        return save(containerDataModel);
    }
}
