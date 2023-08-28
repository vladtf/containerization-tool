import React, { useState, useEffect } from "react";
import { Button, Card, Modal, Spinner } from "react-bootstrap";
import axios from "axios";
import { ToastContainer, toast } from "react-toastify";
import {
  BACKEND_URL,
  PYTHON_BACKEND_URL,
} from "../../config/BackendConfiguration";

const ContainersData = () => {
  const [loading, setLoading] = useState(false);
  const [containers, setContainers] = useState([]);
  const [selectedLogs, setSelectedLogs] = useState([]);
  const [showLogsModal, setShowLogsModal] = useState(false); // State to manage log popup visibility
  const [currentPage, setCurrentPage] = useState(1); // Current page number
  const [totalPages, setTotalPages] = useState(1); // Total number of pages
  const [containerId, setContainerId] = useState(null); // Container ID
  const [pageSize, setPageSize] = useState(30); // Number of logs per page

  const [loadingDelete, setLoadingDelete] = useState(false);

  useEffect(() => {
    fetchFeedbackMessages();
    fetchContainers();

    const refreshInterval = setInterval(() => {
      fetchContainers();
      fetchFeedbackMessages();
    }, 2000); // Refresh data

    return () => {
      clearInterval(refreshInterval);
    };
  }, []);

  const handleDeleteContainer = (containerId) => {
    console.log("Deleting container:", containerId);
    setLoadingDelete(true);
    axios
      .delete(`${PYTHON_BACKEND_URL}/docker/${containerId}`)
      .then((response) => {
        console.log(response);
        toast.success("Deleted container: " + containerId);
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to delete container: " + error.response.data);
      })
      .finally(() => {
        setLoadingDelete(false);
      });

    toast.success("Sent request to delete container: " + containerId);
  };

  const fetchContainers =  () => {
    axios
      .get(`${PYTHON_BACKEND_URL}/docker`)
      .then((response) => {
        console.log(response);
        setContainers(response.data);
      })
      .catch((error) => {
        console.error(error);
        toast.error("Failed to fetch containers: " + error.response.data);
      });
  };

  // This function fetches errors from the backend
  const fetchFeedbackMessages = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/containers/feedback`);
      // Assuming the response contains an array of error messages
      response.data.forEach((message) => {
        if (message.level === "INFO") {
          toast.info(message.message);
        }

        if (message.level === "WARNING") {
          toast.warn(message.message);
        }

        if (message.level === "ERROR") {
          toast.error(message.message);
        }

        if (message.level === "SUCCESS") {
          toast.success(message.message);
        }
      });
    } catch (error) {
      console.error("Failed to fetch errors:", error);
    }
  };

  const fetchContainerLogs = async (containerId, page = 1) => {
    setContainerId(containerId);

    try {
      const response = await axios.get(
        `${BACKEND_URL}/fluentd/logs/${containerId}?page=${page}`
      );
      setSelectedLogs(response.data.content);
      setCurrentPage(response.data.number + 1);
      setTotalPages(response.data.totalPages);
      setPageSize(response.data.size);
      setShowLogsModal(true);
    } catch (error) {
      console.error("Failed to fetch container logs:", error);
      toast.error("Failed to fetch container logs. Please try again later.");
    }
  };

  const handleDeployToAzure = async (container) => {
    console.log("Deploying container:", container);

    setLoading(true);
    axios
      .post(`${PYTHON_BACKEND_URL}/azure/pre-deploy`, container)
      .then((response) => {
        console.log(response);

        // TODO: to show the info about deploy here
        toast.success("Initiated deplot to Azure: " + response.data);

        // Redirect to the azure page
        window.location.href = "/azure?container=" + container.name;
      })
      .catch((error) => {
        console.error(error);
        toast.error(
          "Failed to deploy container to Azure: " + error.response.data
        );
      })
      .finally(() => {
        setLoading(false);
      });

    toast.success("Sent request to deploy container to Azure");
  };

  return (
    <>
      <ToastContainer />
      <Card className="my-4">
        <Card.Body>
          <h3 className="mb-4">Containers</h3>
          {containers.length === 0 ? (
            <p>No containers found.</p>
          ) : (
            containers.map((container, index) => (
              <Card key={index} className="mb-3">
                <Card.Body>
                  <strong>ID:</strong> {container.id}
                  <br />
                  <strong>Name:</strong> {container.name}
                  <br />
                  <strong>Status:</strong> {container.status}
                  <br />
                  <strong>Ip Address:</strong> {container.ip}
                  <br />
                  <strong>Image:</strong> {container.image}
                  <br />
                  <strong>Created At:</strong> {container.created}
                </Card.Body>
                <Card.Footer>
                  <Button
                    onClick={() => fetchContainerLogs(container.id)}
                    variant="outline-primary"
                    style={{ borderRadius: "20px", marginRight: "10px" }}
                  >
                    See Logs
                  </Button>

                  <Button
                    onClick={() => handleDeleteContainer(container.id)}
                    variant="outline-danger"
                    style={{ borderRadius: "20px" }}
                    disabled={loadingDelete}
                  >
                    Delete Container {loadingDelete && <Spinner animation="border" variant="danger" size="sm" />}
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
            ))
          )}
        </Card.Body>
      </Card>

      {/* Log Popup */}
      <Modal
        show={showLogsModal}
        onHide={() => setShowLogsModal(false)}
        size="xl"
      >
        <Modal.Header closeButton>
          <Modal.Title>Container Logs</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <pre
            style={{ background: "#f1f1f1", padding: "1rem", overflow: "auto" }}
          >
            {selectedLogs.map((log, index) => (
              <React.Fragment key={index}>
                <span style={{ display: "inline-block" }}>
                  {currentPage * pageSize - pageSize + index + 1}.
                </span>
                {log.message}
                <br />
              </React.Fragment>
            ))}
          </pre>
        </Modal.Body>
        <Modal.Footer>
          <span>{`Page ${currentPage} of ${totalPages}`}</span>
          <Button
            variant="secondary"
            onClick={() => fetchContainerLogs(containerId, currentPage - 1)}
            disabled={currentPage === 1} // Disable previous button on the first page
          >
            Previous
          </Button>
          <Button
            variant="secondary"
            onClick={() => fetchContainerLogs(containerId, currentPage + 1)}
            disabled={currentPage === totalPages} // Disable next button on the last page
          >
            Next
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default ContainersData;
