import { Button, Card, Container, Spinner, Table } from "react-bootstrap";
import CustomNavbar from "../components/CustomNavbar";
import { ToastContainer, toast } from "react-toastify";
import CustomFooter from "../components/CustomFooter";
import { PYTHON_BACKEND_URL } from "../config/BackendConfiguration";
import axios from "axios";
import { useEffect, useState } from "react";
import { IoCubeOutline } from "react-icons/io5";

const AzurePage = () => {
  const [loading, setLoading] = useState(false);
  const [azureLoading, setAzureLoading] = useState(false);
  const [containers, setContainers] = useState([]);
  const [selectedContainer, setSelectedContainer] = useState("");
  const [azureContainerData, setAzureContainerData] = useState([]);

  useEffect(() => {
    fetchContainers();

    const refreshInterval = setInterval(() => {
      fetchContainers();
    }, 2000); // Refresh data

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  // when selectedContainer changes, fetch azure container data if container is deployed
  useEffect(() => {
    if (selectedContainer) {
      const container = containers.find(
        (container) => container.id === selectedContainer
      );

      if (container.status === "deployed") {
        setAzureLoading(true);
        axios
          .get(`${PYTHON_BACKEND_URL}/azure/container/${container.id}`)
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
      }
    }
  }, [selectedContainer]);

  const fetchContainers = async () => {
    try {
      const response = await axios.get(`${PYTHON_BACKEND_URL}/azure/all`);
      setContainers(response.data);
    } catch (error) {
      console.error("Failed to fetch containers:", error);
      toast.error("Failed to fetch containers. Please try again later.");
    }
  };

  const handleDeployToAzure = async (container) => {
    console.log("Deploying container:", container);

    setLoading(true);
    axios
      .post(`${PYTHON_BACKEND_URL}/azure/deploy`, container)
      .then((response) => {
        console.log(response);

        // TODO: to show the info about deploy here
        toast.success("Initiated deplot to Azure: " + response.data);
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

  const handleDeleteContainer = async (containerId) => {
    console.log("Deleting container:", containerId);
    toast.success("TODO: Delete container: " + containerId);
  };

  const container = containers.find(
    (container) => container.id === selectedContainer
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
                onClick={() => setSelectedContainer(container.id)}
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

      {selectedContainer && (
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
          <Card.Footer>
            <Button
              onClick={() => handleDeleteContainer(container.id)}
              variant="outline-danger"
              style={{ borderRadius: "20px" }}
            >
              Delete Container
            </Button>
            <Button
              onClick={() => handleDeployToAzure(container)}
              variant="outline-success"
              style={{ borderRadius: "20px", marginLeft: "10px" }}
            >
              Deploy to Azure{" "}
              {loading && (
                <Spinner animation="border" variant="success" size="sm" />
              )}
            </Button>
          </Card.Footer>
        </Card>
      )}

      <CustomFooter />
    </Container>
  );

  function renderContainerSelectionVariant(container) {
    // if container is deployed
    if (container.status === "deployed") {
      return container.id === selectedContainer ? "success" : "outline-success";
    }

    // if container is not deployed
    return container.id === selectedContainer
      ? "secondary"
      : "outline-secondary";
  }
};

export default AzurePage;
