import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import axios from "axios";
import { useEffect, useState } from "react";
import { Button, Card, Container, Spinner, Table } from "react-bootstrap";
import { IoCubeOutline } from "react-icons/io5";
import { ToastContainer, toast } from "react-toastify";
import CustomFooter from "../components/CustomFooter";
import CustomNavbar from "../components/CustomNavbar";
import { PYTHON_BACKEND_URL } from "../config/BackendConfiguration";

const AzurePage = () => {
  const [loading, setLoading] = useState(false);
  const [azureLoading, setAzureLoading] = useState(false);
  const [containers, setContainers] = useState([]);
  const [selectedContainer, setSelectedContainer] = useState("");
  const [azureContainerData, setAzureContainerData] = useState([]);

  const [selectedRepository, setSelectedRepository] = useState("");
  const [selectedInstance, setSelectedInstance] = useState("");

  const [azureContainerInstances, setAzureContainerInstances] = useState([]);
  const [loadingInstances, setLoadingInstances] = useState(true);

  const [azureContainerRepositories, setAzureContainerRepositories] = useState(
    []
  );
  const [loadingRepositories, setLoadingRepositories] = useState(true);

  const [openDeleteContainerDialog, setOpenDeleteContainerDialog] =
    useState(false);

  const [openUndeployContainerDialog, setOpenUndeployContainerDialog] =
    useState(false);

  const [openDeleteRepositoryDialog, setOpenDeleteRepositoryDialog] =
    useState(false);

  const [openDeleteInstanceDialog, setOpenDeleteInstanceDialog] =
    useState(false);

  useEffect(() => {
    fetchContainers();
    fetchAzureContainerInstances();
    fetchAzureContainerRepositories();

    const selectedContainerFromUrl = new URLSearchParams(
      window.location.search
    ).get("container");

    if (selectedContainerFromUrl) {
      setSelectedContainer(selectedContainerFromUrl);
    }

    const refreshInterval = setInterval(() => {
      fetchContainers();
      fetchAzureContainerInstances();
      fetchAzureContainerRepositories();
    }, 5000); // Refresh data

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  // when selectedContainer changes, fetch azure container data if container is deployed
  useEffect(() => {
    if (selectedContainer) {
      const container = containers.find(
        (container) => container.name === selectedContainer
      );

      if (!container) {
        return;
      }

      if (container.status === "deployed") {
        fetchAzureContainerData(selectedContainer);
      }
    }
  }, [selectedContainer]);

  const fetchAzureContainerData = async (containerId) => {
    if (!containerId) {
      return;
    }

    console.log("Fetching Azure container data:", containerId);

    setAzureLoading(true);
    axios
      .get(`${PYTHON_BACKEND_URL}/azure/container/${containerId}`)
      .then((response) => {
        console.log(response);
        setAzureContainerData(response.data);
      })
      .catch((error) => {
        console.error(error);
        toast.error(
          "Failed to fetch Azure container data: " + error.response.data
        );
      })
      .finally(() => {
        setAzureLoading(false);
      });
  };

  const fetchContainers = async () => {
    try {
      const response = await axios.get(`${PYTHON_BACKEND_URL}/azure/all`);
      setContainers(response.data);
    } catch (error) {
      console.error("Failed to fetch containers:", error);
      toast.error("Failed to fetch containers. Please try again later.");
    }
  };

  const fetchAzureContainerInstances = () => {
    console.log("Fetching Azure container instances");

    // setLoadingInstances(true);
    axios
      .get(`${PYTHON_BACKEND_URL}/azure/instances`)
      .then((response) => {
        console.log(response);
        setAzureContainerInstances(response.data);
      })
      .catch((error) => {
        console.error(error);
        toast.error(
          "Failed to fetch Azure container instances: " + error.response.data
        );
      })
      .finally(() => {
        setLoadingInstances(false);
      });
  };

  const fetchAzureContainerRepositories = () => {
    console.log("Fetching Azure container repositories");

    // setLoadingRepositories(true);
    axios
      .get(`${PYTHON_BACKEND_URL}/azure/repositories`)
      .then((response) => {
        console.log(response);
        setAzureContainerRepositories(response.data);
      })
      .catch((error) => {
        console.error(error);
        toast.error(
          "Failed to fetch Azure container repositories: " + error.response.data
        );
      })
      .finally(() => {
        setLoadingRepositories(false);
      });
  };

  const handleDeleteRepository = (repositoryName) => {
    console.log("Deleting repository:", repositoryName);
    toast.success("Deleting repository: " + repositoryName);

    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/repository/${repositoryName}`)
      .then((response) => {
        console.log(response);
        toast.success(
          "Repository '" + repositoryName + "' deleted successfully"
        );
        fetchAzureContainerRepositories();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete repository: " + error.response.data);
      });
  };

  const handleDeleteContainerInstance = (instanceName) => {
    console.log("Deleting instance:", instanceName);
    toast.success("Deleting instance: " + instanceName);

    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/instances/${instanceName}`)
      .then((response) => {
        console.log(response);
        toast.success("Instance '" + instanceName + "' deleted successfully");
        fetchAzureContainerInstances();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete instance: " + error.response.data);
      });
  };

  const handleDeployToAzure = async (container) => {
    console.log("Deploying container:", container);

    setLoading(true);
    axios
      .post(`${PYTHON_BACKEND_URL}/azure/deploy`, container)
      .then((response) => {
        console.log(response);

        // TODO: to show the info about deploy here
        toast.success("Container deployed successfully: " + response.data);
        fetchAzureContainerData(container.id);
      })
      .catch((error) => {
        console.error(error);
        toast.error(
          "Failed to deploy container to Azure: " + error.response.data
        );
      })
      .finally(() => {
        setLoading(false);
        fetchContainers();
      });

    toast.success("Sent request to deploy container to Azure");
  };

  const handleDeleteContainer = async (container) => {
    const containerId = container.id;

    console.log("Deleting container:", containerId);

    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/container/${containerId}`)
      .then((response) => {
        console.log(response);
        toast.success("Container deleted successfully");

        setSelectedContainer("");
        fetchContainers();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete container: " + error.response.data);
      });
  };

  const handleUndeployContainer = async (container) => {
    const containerId = container.id;

    console.log("Undeploying container:", containerId);

    setLoading(true);
    axios
      .delete(`${PYTHON_BACKEND_URL}/azure/deploy/${containerId}`)
      .then((response) => {
        console.log(response);
        toast.success("Container undeployed successfully");
        fetchContainers();
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to undeploy container: " + error.response.data);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const fetchContainerLogs = async (container) => {
    console.log("Fetching container logs:", container);
    toast.success("TODO: Fetch container logs: " + container);
  };

  const container = containers.find(
    (container) => container.name === selectedContainer
  );

  return (
    <Container>
      <CustomNavbar />
      <ToastContainer />

      <Card className="my-4">
        <Card.Body>
          <h3>Containers</h3>

          <hr />

          <div style={{ overflowX: "scroll", display: "flex" }}>
            {containers.map((container) => (
              <Button
                key={container.id}
                style={{
                  margin: "0 5px",
                  width: "180px",
                  height: "180px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  position: "relative",
                }}
                variant={renderContainerSelectionVariant(container)}
                onClick={() => setSelectedContainer(container.name)}
              >
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: "50%",
                    transform: "translateX(-50%)",
                  }}
                >
                  <IoCubeOutline size={40} />
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "100%",
                  }}
                >
                  <span>{container.name}</span>
                </div>
              </Button>
            ))}
          </div>

          <hr />
        </Card.Body>
      </Card>

      {selectedContainer && container && (
        <Card className="mb-3">
          <Card.Body>
            <h5>ID: {container.id}</h5>
            <p>
              <strong>Name:</strong> {container.name}
            </p>
            <p>
              <strong>Status:</strong> {container.status}
            </p>
            <p>
              <strong>Image:</strong> {container.image}
            </p>
            {/* If container is in 'deployed' status then fetch azure container data */}
            {container.status === "deployed" && (
              <>
                <hr />
                {azureLoading ? (
                  <>
                    <br />
                    <Spinner animation="border" variant="primary" size="md" />
                  </>
                ) : (
                  <div style={{ overflowX: "auto" }}>
                    <Table striped bordered hover responsive>
                      <thead>
                        <tr>
                          <th>Attribute</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>
                            <strong>ID:</strong>
                          </td>
                          <td>{azureContainerData.instance_id}</td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Name:</strong>
                          </td>
                          <td>{azureContainerData.instance_name}</td>
                        </tr>
                        <tr>
                          <td>
                            <strong>IP:</strong>
                          </td>
                          <td>{azureContainerData.instance_ip ?? "N/A"}</td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Ports:</strong>
                          </td>
                          <td>{azureContainerData.instance_ports}</td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Status:</strong>
                          </td>
                          <td>{azureContainerData.instance_status}</td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Start Time:</strong>
                          </td>
                          <td>{azureContainerData.instance_start_time}</td>
                        </tr>
                        <tr>
                          <td>
                            <strong>Image:</strong>
                          </td>
                          <td>{azureContainerData.instance_image}</td>
                        </tr>
                      </tbody>
                    </Table>
                  </div>
                )}
              </>
            )}
          </Card.Body>
          <Card.Footer>{renderContainersButtons(container)}</Card.Footer>
        </Card>
      )}

      {/* Component to display all the container instances in a table with delete button */}
      <Card className="mb-3">
        <Card.Body>
          <h5>Container Instances</h5>
          <hr />
          <div style={{ overflowX: "auto" }}>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  {/* <th>Instance ID</th> */}
                  <th>Instance Name</th>
                  <th>Instance Image</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {azureContainerInstances.map((instance) => (
                  <tr key={instance.id}>
                    {/* <td>{instance.id}</td> */}
                    <td>{instance.name}</td>
                    <td>{instance.image}</td>
                    <td>
                      <Button
                        onClick={() => {
                          setSelectedInstance(instance.name);
                          setOpenDeleteInstanceDialog(true);
                        }}
                        variant="outline-danger"
                        style={{ borderRadius: "20px" }}
                      >
                        Delete Instance
                      </Button>
                    </td>
                  </tr>
                ))}
                {loadingInstances && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: "center" }}>
                      <Spinner animation="border" variant="primary" size="md" />
                    </td>
                  </tr>
                )}

                {/* if no instances are present and loading is false */}
                {!loadingInstances && azureContainerInstances.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: "center" }}>
                      No instances found
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          </div>
        </Card.Body>
      </Card>

      {/* Component to display all the container repositories in a table with delete button */}
      <Card className="mb-3">
        <Card.Body>
          <h5>Container Repositories</h5>
          <hr />
          <div style={{ overflowX: "auto" }}>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>Reposiory Name</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {azureContainerRepositories.map((repository) => (
                  <tr key={repository.name}>
                    <td>{repository.name}</td>
                    <td>
                      <Button
                        onClick={() => {
                          setSelectedRepository(repository.name);
                          setOpenDeleteRepositoryDialog(true);
                        }}
                        variant="outline-danger"
                        style={{ borderRadius: "20px" }}
                      >
                        Delete Repository
                      </Button>
                    </td>
                  </tr>
                ))}
                {loadingRepositories && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: "center" }}>
                      <Spinner animation="border" variant="primary" size="md" />
                    </td>
                  </tr>
                )}

                {/* if no repositories are present and loading is false */}
                {!loadingRepositories &&
                  azureContainerRepositories.length === 0 && (
                    <tr>
                      <td colSpan={4} style={{ textAlign: "center" }}>
                        No repositories found
                      </td>
                    </tr>
                  )}
              </tbody>
            </Table>
          </div>
        </Card.Body>
      </Card>

      <Dialog
        open={openDeleteContainerDialog}
        onClose={() => setOpenDeleteContainerDialog(false)}
      >
        <DialogTitle>Delete Container</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this container:
            {container && container.name}?
          </DialogContentText>
        </DialogContent>

        <DialogActions>
          <Button
            variant="primary"
            onClick={() => setOpenDeleteContainerDialog(false)}
          >
            Cancel
          </Button>
          <Button
            variant="outline-danger"
            onClick={() => {
              setOpenDeleteContainerDialog(false);
              handleDeleteContainer(container);
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* dialog to confirm undeploy container */}
      <Dialog
        open={openUndeployContainerDialog}
        onClose={() => setOpenUndeployContainerDialog(false)}
      >
        <DialogTitle>Undeploy Container</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to undeploy this container:
            {container && container.name}?
          </DialogContentText>
        </DialogContent>

        <DialogActions>
          <Button
            variant="primary"
            onClick={() => setOpenUndeployContainerDialog(false)}
          >
            Cancel
          </Button>
          <Button
            variant="outline-danger"
            onClick={() => {
              setOpenUndeployContainerDialog(false);
              handleUndeployContainer(container);
            }}
          >
            Undeploy
          </Button>
        </DialogActions>
      </Dialog>

      {/* dialog to confirm delete repository */}
      <Dialog
        open={openDeleteRepositoryDialog}
        onClose={() => setOpenDeleteRepositoryDialog(false)}
      >
        <DialogTitle>Delete Repository</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this repository:{" "}
            {selectedRepository}?
          </DialogContentText>
        </DialogContent>

        <DialogActions>
          <Button
            variant="primary"
            onClick={() => setOpenDeleteRepositoryDialog(false)}
          >
            Cancel
          </Button>
          <Button
            variant="outline-danger"
            onClick={() => {
              setOpenDeleteRepositoryDialog(false);
              handleDeleteRepository(selectedRepository);
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* dialog to confirm delete instance */}
      <Dialog
        open={openDeleteInstanceDialog}
        onClose={() => setOpenDeleteInstanceDialog(false)}
      >
        <DialogTitle>Delete Instance</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this instance: {selectedInstance}?
          </DialogContentText>
        </DialogContent>

        <DialogActions>
          <Button
            variant="primary"
            onClick={() => setOpenDeleteInstanceDialog(false)}
          >
            Cancel
          </Button>
          <Button
            variant="outline-danger"
            onClick={() => {
              setOpenDeleteInstanceDialog(false);
              handleDeleteContainerInstance(selectedInstance);
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      <CustomFooter />
    </Container>
  );

  function renderContainerSelectionVariant(container) {
    // if container is deployed
    if (container.status === "deployed") {
      return container.name === selectedContainer
        ? "success"
        : "outline-success";
    }

    // if container is not deployed
    return container.name === selectedContainer
      ? "secondary"
      : "outline-secondary";
  }

  function renderContainersButtons(container) {
    // if container is ready show delete and deploy buttons
    if (container.status === "ready") {
      return (
        <>
          <Button
            onClick={() => setOpenDeleteContainerDialog(true)}
            variant="outline-danger"
            style={{ borderRadius: "20px" }}
          >
            Delete Container
          </Button>
          <Button
            onClick={() => handleDeployToAzure(container)}
            variant="outline-success"
            style={{ borderRadius: "20px", marginLeft: "10px" }}
            disabled={loading}
          >
            Deploy to Azure{" "}
            {loading && (
              <Spinner animation="border" variant="success" size="sm" />
            )}
          </Button>
        </>
      );
    }

    // if container is deployed show un-deploy button and logs button
    if (container.status === "deployed") {
      return (
        <>
          <Button
            onClick={() => setOpenUndeployContainerDialog(true)}
            variant="outline-danger"
            style={{ borderRadius: "20px" }}
            disabled={loading}
          >
            Undeploy from Azure{" "}
            {loading && (
              <Spinner animation="border" variant="danger" size="sm" />
            )}
          </Button>
          <Button
            onClick={() => fetchContainerLogs(container)}
            variant="outline-primary"
            style={{ borderRadius: "20px", marginLeft: "10px" }}
          >
            See Logs
          </Button>
        </>
      );

      // if container is not ready or deployed show nothing
    } else {
      return null;
    }
  }
};

export default AzurePage;
